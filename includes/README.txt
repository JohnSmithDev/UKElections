What's the difference between the /static/ and /includes/ subdirectories?

/static/ is intended for resources that can reasonably exist as useful files in
their own right - CSS and JavaScript files are good examples.

/includes/ is for snippets that can only exist as fragments included in a larger
(typically HTML or SVG) document.

The build process that aims to create complete standalone HTML or SVG files
containing these resources perhaps blurs things - the difference would be
perhaps more obvious in a regular website that happily includes external
resources via '<link rel=...>' or '<script src=...>' etc

Don't get too worried about putting things in the wrong subdirectory though,
at least not whilst there are still relatively few files to worry about.

