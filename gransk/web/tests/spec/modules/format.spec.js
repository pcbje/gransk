describe("format", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var format;

  beforeEach(inject(function(config, _format_) {
    format = _format_
  }));

  it('parses key containing "size" as size', function() {
    var expected = '1.0 KB';
    var actual = format.auto('file_size', 1024)
    expect(actual).toEqual(expected)
  });

  it('parses string date as date', function() {
    var expected = '2015-11-17 00:00:00';
    var actual = format.auto('date', '2015/11/17 00:00')
    expect(actual).toEqual(expected)
  });

  it('parses unix timestamp as date', function() {
    var expected = '2009-02-14';
    var actual = format.auto('mock', 1234577891).substring(0, 10)
    expect(actual).toEqual(expected)
  });


  it('parses size bytes', function() {
    expect(format.size(916)).toEqual('916 bytes')
  });

  it('parses size kilo bytes', function() {
    expect(format.size(9160)).toEqual('8.9 KB')
  });

  it('parses size mega bytes', function() {
    expect(format.size(9160 * 1024)).toEqual('8.9 MB')
  });

  it('parses size giga bytes', function() {
    expect(format.size(9160 * 1024 * 1024)).toEqual('8.9 GB')
  });

  it('parses recent date seconds', function() {
    var now = new Date();
    var then = new Date(now.getTime() - 40 * 1000);
    expect(format.time(now, then)).toEqual('40 seconds ago')
  });

  it('parses recent date minutes', function() {
    var now = new Date();
    var then = new Date(now.getTime() - 40 * 60 * 1000);
    expect(format.time(now, then)).toEqual('40 minutes ago')
  });

  it('parses recent date hours', function() {
    var now = new Date();
    var then = new Date(now.getTime() - 40 * 60 * 4 * 1000);
    expect(format.time(now, then)).toEqual('3 hours ago')
  });

  it('parses recent date days', function() {
    var now = new Date();
    var then = new Date(now.getTime() - 40 * 60 * 24 * 3 * 1000);
    expect(format.time(now, then)).toEqual('2 days ago')
  });

  it('parses date more than one week ago', function() {
    var now = new Date('2016-11-09T00:00:00Z');
    var then = new Date(now.getTime() - 60 * 60 * 24 * 60 * 1000); // 60 days
    expect(format.time(now, then).substring(0, 10)).toEqual('2016-09-10')
  });
});
