import { useEffect, useRef } from "react";

/**
 * WebGL fluid backdrop. A single full-screen triangle running an fbm + domain-
 * warp fragment shader in the brand palette: the drifting "control-plane"
 * nebula behind the app. Raw WebGL (no three.js) so it stays a few KB and 60fps.
 * Honors prefers-reduced-motion (renders one static frame) and pauses when the
 * tab is hidden.
 */
const FRAG = `
precision highp float;
uniform vec2 u_res;
uniform float u_time;

// hash / value-noise / fbm
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
float noise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hash(i+vec2(0,0)), hash(i+vec2(1,0)), u.x),
             mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  for(int i=0;i<5;i++){ v += a*noise(p); p *= 2.02; a *= 0.5; }
  return v;
}

void main(){
  vec2 uv = gl_FragCoord.xy / u_res.xy;
  vec2 p = uv;
  p.x *= u_res.x / u_res.y;
  float t = u_time * 0.02;

  // domain warp for a fluid, smoky feel
  vec2 q = vec2(fbm(p + vec2(0.0, t)), fbm(p + vec2(5.2, -t)));
  vec2 r = vec2(fbm(p + 1.8*q + vec2(1.7, 9.2) + 0.15*t),
                fbm(p + 1.8*q + vec2(8.3, 2.8) - 0.12*t));
  float f = fbm(p + 2.4*r);

  // brand palette: deep base -> blue -> cyan -> teal highlight (no violet)
  vec3 base = vec3(0.030, 0.040, 0.058);
  vec3 blue = vec3(0.050, 0.115, 0.235);
  vec3 cyan = vec3(0.075, 0.360, 0.470);
  vec3 teal = vec3(0.085, 0.470, 0.415);

  vec3 col = base;
  col = mix(col, blue, smoothstep(0.15, 0.75, f));
  col = mix(col, cyan, smoothstep(0.35, 0.95, length(r)));
  col = mix(col, teal, smoothstep(0.70, 1.05, f + 0.35*q.x));

  // radial vignette keeps the center readable and edges deep
  float vig = smoothstep(1.25, 0.25, distance(uv, vec2(0.5)));
  col *= 0.35 + 0.65*vig;

  // subtle grain to kill banding
  col += (hash(gl_FragCoord.xy + u_time) - 0.5) * 0.02;

  gl_FragColor = vec4(col, 1.0);
}
`;

const VERT = `
attribute vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

export function Backdrop() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false });
    if (!gl) return;

    const compile = (type: number, src: string) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    // one big triangle covering the viewport
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "a_pos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(prog, "u_res");
    const uTime = gl.getUniformLocation(prog, "u_time");

    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const resize = () => {
      const w = Math.floor(window.innerWidth * dpr);
      const h = Math.floor(window.innerHeight * dpr);
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
      gl.uniform2f(uRes, w, h);
    };
    resize();
    window.addEventListener("resize", resize);

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let raf = 0;
    let hidden = false;
    const onVis = () => (hidden = document.hidden);
    document.addEventListener("visibilitychange", onVis);

    const start = performance.now();
    const draw = () => {
      if (!hidden) {
        gl.uniform1f(uTime, (performance.now() - start) / 1000);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
      raf = requestAnimationFrame(draw);
    };
    if (reduce) {
      gl.uniform1f(uTime, 12.0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    } else {
      draw();
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return <canvas ref={ref} className="backdrop" aria-hidden />;
}
