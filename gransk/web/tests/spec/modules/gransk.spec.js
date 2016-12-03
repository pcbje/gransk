describe("gransk", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var _config;
  var _stats;
  var _docs;
  var _entity;
  var _client;
  var _scope;
  var $filter;
  var $compile;

  beforeEach(inject(function(config, stats, doc, entity, $controller, $rootScope, _$filter_, _$compile_) {
    _config = config;
    _stats = stats;
    _doc = doc;
    _entity = entity;
    _scope = $rootScope.$new();
    $filter = _$filter_;
    $compile = _$compile_;

    spyOn(_stats, 'load').andCallFake(function(callback) {
      callback('mock stats');
    });

    $controller('MainCtrl', {
      $scope: _scope
    });
  }));

  it('should convert highlight to html', function() {
    var text = 'mock [[a href=""]]MOCK 1[[/a]] [[a href=""]]MOCK 2[[/a]] mock';
    var expected = 'mock <a href="">MOCK 1</a> <a href="">MOCK 2</a> mock';
    var actual = $filter('to_trusted')(text).$$unwrapTrustedValue();
    expect(actual).toEqual(expected);
  });

  it('should load statistics on init', function() {
    expect(_scope.statistics).toEqual('mock stats');
  });

  it('should highlight text', function() {
    var actual = _scope.highlight('dummy', 'a dummy dummy highlight');
    var expected = 'a [[span]]dummy[[/span]] [[span]]dummy[[/span]] highlight';
    expect(actual).toEqual(expected);
  });

  it('should prettify json object', function() {
    var expected = 'a\nb';
    var actual = _scope.prettify('mock', {
      'a': 1,
      'b': 2
    });
    expect(expected).toEqual(actual);
  });

  it('should not prettify string', function() {
    var expected = 'a b c';
    var actual = _scope.prettify('mock', 'a b c');
    expect(expected).toEqual(actual);
  });


  it('should set title from mode', function() {
    _scope.mode = 'mock';
    _scope.$apply();
    expect(_scope.title).toEqual(_config.app_title + ' | Mock');
  });

  it('should submit query', function() {
    spyOn(_doc, 'search').andCallFake(function(query, page, facets, callback) {
      callback({
        total: 4
      });
    });

    spyOn(_entity, 'search').andCallFake(function(query, page, facets, callback) {
      callback({
        total: 2
      });
    });

    _scope.document_page = -1;
    _scope.form_submit_query('mock');
    expect(_scope.document_page).toEqual(0);

    expect(_doc.search).toHaveBeenCalled();
    expect(_entity.search).toHaveBeenCalled();

    expect(_scope.counts).toEqual({
      entities: 2,
      documents: 4
    });
  });

  it('should compile file upload directive', function() {
    var element = $compile('<dropzone></dropzone>')(_scope);
    _scope.$apply();

    expect(element.html()).toContain('id="upload-progress"');

    var s = element.isolateScope();

    expect(s.progress_bar.style.display).toEqual('none');

    s.dz.emit('addedfile', {});
    s.dz.emit('addedfile', {});

    expect(s.added).toEqual(2);
    expect(s.completed).toEqual(0);
    expect(s.progress).toEqual(0);
    expect(s.progress_bar.style.display).toEqual('block');


    s.dz.emit('complete', {});

    expect(s.added).toEqual(2);
    expect(s.completed).toEqual(1);
    expect(s.progress).toEqual(50);

    s.dz.emit('complete', {});
  });
});
