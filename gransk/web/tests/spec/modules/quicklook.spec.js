describe("quicklook", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  beforeEach(inject(function(_$compile_, _$rootScope_, _$injector_, _text_selection_, _client_) {
    $compile = _$compile_;
    $rootScope = _$rootScope_;
    $injector = _$injector_;
    text_selection = _text_selection_;
    client = _client_;
  }));


  it('opens quicklook', function() {
    var scope = $rootScope.$new();
    $httpBackend = $injector.get('$httpBackend');
    $httpBackend.when('GET', '/static/views/quicklook.html').respond('<div></div>');

    var _callback;
    var searches = 0;

    spyOn(text_selection, 'listen').andCallFake(function(id, callback) {
      _callback = callback;
    });

    spyOn(automagic, 'generate').andCallFake(function() {
      return {}
    })

    spyOn(client, 'search').andCallFake(function() {
      searches++;

      return {then: function(callback){ callback({hits: []})}}
    })

    var elem = document.createElement('div');

    spyOn(document, 'getElementsByClassName').andCallFake(function() {
      return {
        length: 1,
        item: function() {return elem}
      }
    });

    var element = $compile('<quicklook search="submit_query(query)" lock="lock"></quicklook')(scope);
    scope.$apply();

    $httpBackend.flush();

    _callback('jubajuba')

    // One for documents and one for entities.
    expect(searches).toEqual(2);
    expect(elem.getAttribute('name')).toEqual('withquick');
  });
});
