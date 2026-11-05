// Copy next to primer.js and scripts/apply_theme.js; install pptxgenjs@4.0.1 locally.
const pptxgen = require('pptxgenjs');
const P = require('./primer.js');
const { applyTheme } = require('./scripts/apply_theme.js');
(async () => {
  const output = process.argv[2] || 'Example.pptx';
  const pres = new pptxgen();
  P.setup(pres, {title: 'Example presentation', footer: 'Example presentation'});
  let slide = pres.addSlide({masterName: 'DARK'});
  slide.addText('Example presentation', {x: P.M, y: 1.7, w: 9, h: 0.9,
    fontFace: P.FONT, fontSize: P.TYPE.display, bold: true, color: P.DARK.fg, margin: 0});
  slide = pres.addSlide({masterName: 'LIGHT'});
  slide.addText('One clear idea per slide', {placeholder: 'title'});
  P.rows(pres, slide, P.M, 1.5, 8.5, [
    ['Point', 'Keep the text short enough to read from the back of the classroom.'],
    ['Image', 'Use a genuine image of the subject and credit its source.'],
  ], {pitch: 1, size: P.TYPE.lead});
  await pres.writeFile({fileName: output});
  await applyTheme(output, P.THEME);
  console.log(output);
})();
