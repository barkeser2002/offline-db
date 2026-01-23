export const Anime4KShaderSource = {
  vertex: `
    attribute vec2 a_position;
    attribute vec2 a_texCoord;
    varying vec2 v_texCoord;
    void main() {
      gl_Position = vec4(a_position, 0, 1);
      v_texCoord = a_texCoord;
    }
  `,
  fragment: `
    precision mediump float;
    uniform sampler2D u_image;
    varying vec2 v_texCoord;
    uniform vec2 u_textureSize;

    // Simple sharpening kernel (approximation of Anime4K logic for demo)
    void main() {
      vec2 onePixel = vec2(1.0, 1.0) / u_textureSize;
      
      vec4 color = texture2D(u_image, v_texCoord);
      vec4 colorLeft = texture2D(u_image, v_texCoord - vec2(onePixel.x, 0.0));
      vec4 colorRight = texture2D(u_image, v_texCoord + vec2(onePixel.x, 0.0));
      vec4 colorUp = texture2D(u_image, v_texCoord - vec2(0.0, onePixel.y));
      vec4 colorDown = texture2D(u_image, v_texCoord + vec2(0.0, onePixel.y));
      
      // Basic unsharp mask
      vec4 blur = (colorLeft + colorRight + colorUp + colorDown) * 0.25;
      vec4 diff = color - blur;
      gl_FragColor = color + diff * 1.5; // Enhance contrast/edges
    }
  `
};
