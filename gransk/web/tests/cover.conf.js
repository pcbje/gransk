'use strict';

module.exports = function (config) {
  config.set({
    basePath: '../app/',
    logLevel: config.LOG_INFO,
    frameworks: ['jasmine'],
    singleRun: true,
    files: [
        'lib/angular.min.js',
        'lib/*.js',
        'modules/gransk.js',
        'modules/*.js',
        '../tests/spec/lib/*.js',
        '../tests/spec/modules/*.js',
    ],
    exclude: [],
    browsers: ['PhantomJS'],
    reporters: ['progress', 'coverage'],
    coverageReporter: {
      reporters: [
        { type: 'lcovonly', dir: '../../../coverage/web', subdir: '.', file: 'lcov.info' },
      ]
    },
    preprocessors: {
        'modules/*.js': ['coverage'],
        '*.html': ['ng-html2js']
    }
  })
};
