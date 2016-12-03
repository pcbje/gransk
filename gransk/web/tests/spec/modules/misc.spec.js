describe("misc modules", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var _config;

  beforeEach(inject(function(config) {
    _config = config;
  }));

  describe("text_selection", function() {
    var text_selection;
    beforeEach(inject(function(_text_selection_) {
      text_selection = _text_selection_;
    }));

    it('should send selected text to listeners', function() {
      var result = []

      text_selection.clear();
      text_selection.listen('mock', function(text) {
        result.push(text);
      });

      spyOn(window, 'getSelection').andReturn({
        getRangeAt: function() {
          return {
            commonAncestorContainer: {data: 'abcdef', getAttribute: function(attr) {
              if (attr === 'class') return 'searchable';
              return 'other';
            }},
            startOffset: 1,
            endOffset: 5,
          };
        }
      });

      var evt = new CustomEvent("mouseup");

      window.dispatchEvent(evt);

      expect(result).toEqual(['bcde']);
    });
  });

  describe("hotkeys", function() {
    var _hotkeys;

    beforeEach(inject(function(hotkeys) {
      _hotkeys = hotkeys;
    }));

    it('should fire event to listeners', function() {
      var expected_action;
      var calls = 0;

      _hotkeys.clear();
      _hotkeys.listen(function(action) {
        expect(expected_action).toEqual(action);
        calls += 1;
      });

      var evt = new CustomEvent("keydown");

      evt.key = '<';
      expected_action = 'up';
      window.dispatchEvent(evt);
      evt.key = 'z';
      expected_action = 'down';
      window.dispatchEvent(evt);
      evt.key = 'n';
      expected_action = 'next';
      window.dispatchEvent(evt);
      evt.key = 'p';
      expected_action = 'prev';
      window.dispatchEvent(evt);
      evt.key = 'other';
      expected_action = null;
      window.dispatchEvent(evt);

      expect(calls).toEqual(4);
    });

    it('get down - more items', function() {
      var current_index = 1;
      var expected_index = 2;
      var actual = _hotkeys.get('down', 3, 0, 0, current_index);
      expect(expected_index).toEqual(actual.index);
    });

    it('get down - max index - more pages', function() {
      var current_index = 2;
      var expected = {
        page: 1,
        index: 0
      };
      var actual = _hotkeys.get('down', 3, 1, 0, current_index);
      expect(expected).toEqual(actual);
    });

    it('get down - max index - no more pages', function() {
      var current_index = 2;
      var expected = {
        index: 2
      };
      var actual = _hotkeys.get('down', 3, 0, 0, current_index);
      expect(expected).toEqual(actual);
    });

    it('get up - more items', function() {
      var current_index = 1;
      var expected_index = 0;
      var actual = _hotkeys.get('up', 3, 0, 0, current_index);
      expect(expected_index).toEqual(actual.index);
    });

    it('get down - min index - has prev page', function() {
      var current_index = 0;
      var current_page = 1;
      var expected = {
        page: 0,
        index: _config.pagesize - 1
      };
      var actual = _hotkeys.get('up', 3, 1, current_page, current_index);
      expect(expected).toEqual(actual);
    });

    it('get down - min index - no prev page', function() {
      var current_index = 0;
      var current_page = 0;
      var expected = {
        index: 0
      };
      var actual = _hotkeys.get('up', 3, 1, current_page, current_index);
      expect(expected).toEqual(actual);
    });

    it('next page - more pages', function() {
      var current_page = 0;
      var expected = {
        page: 1,
        index: 0
      };
      var actual = _hotkeys.get('next', 3, 1, current_page, 0);
      expect(expected).toEqual(actual);
    });

    it('next page - no more pages', function() {
      var current_page = 1;
      var expected = {};
      var actual = _hotkeys.get('next', 3, 1, current_page, 0);
      expect(expected).toEqual(actual);
    });

    it('prev page - has prev page', function() {
      var current_page = 1;
      var expected = {
        page: 0,
        index: 0
      };
      var actual = _hotkeys.get('prev', 3, 1, current_page, 0);
      expect(expected).toEqual(actual);
    });

    it('next page - no prev page', function() {
      var current_page = 0;
      var expected = {};
      var actual = _hotkeys.get('prev', 3, 1, current_page, 0);
      expect(expected).toEqual(actual);
    });
  });

  describe("pagecount", function() {
    var _pagecount;

    beforeEach(inject(function(pagecount) {
      _pagecount = pagecount;
    }));

    it('number of pages items % pagecount != 0', function() {
      _config.pagesize = 4;
      var expected = 2;
      var actual = _pagecount.compute(10);
      expect(actual).toEqual(expected);
    });

    it('number of pages items % pagecount === 0', function() {
      _config.pagesize = 5;
      var expected = 1;
      var actual = _pagecount.compute(10);
      expect(expected).toEqual(actual);
    });
  });

  describe("aggs", function() {
    var _aggs;

    beforeEach(inject(function(aggs) {
      _aggs = aggs;
    }));

    it('generate aggregation object', function() {
      _config.aggregation_fields = ['mock'];
      _config.aggregation_size = 13;
      var expected = 13;
      var actual = _aggs.get(true).mock.terms.size;
      expect(expected).toEqual(actual);
    });
  });

  describe("related", function() {
    var _related;
    var $httpBackend;

    beforeEach(inject(function($injector, related) {
      _related = related;
      $httpBackend = $injector.get('$httpBackend');
      $httpBackend.when('GET', '/related?type=document&id=mock').respond([{
        id: 'other',
        ref: 'other\x00type',
        type: 'type',
        score: 0.3,
        shared: ['["a"]', '["b"]', '["c"]']
      }, {
        id: 'dummy',
        ref: 'dummy\x00type',
        type: 'type',
        score: 0.2,
        shared: ['["b"]', '["c"]']
      }]);
    }));

    afterEach(function() {
      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
    });

    it('get two related objects', function() {
      $httpBackend.expectGET('/related?type=document&id=mock');
      _related.load('document', 'mock', function(rel) {
        var expected = 2;
        var actual = rel.data.length;
        expect(expected).toEqual(actual);
      });
      $httpBackend.flush();
    });
  });

  describe("query", function() {
    var _query;

    beforeEach(inject(function(query) {
      _query = query;
    }));

    it('test facets', function() {
      var query_obj = _query.generate('type', 'field', '', [], 0, {
        mock_type: {
          mock_value: true,
          other_value: false
        }
      });

      var expected = {
        bool : {
          must : [
            { match_all : {  } },
            { terms : { mock_type : [ 'mock_value' ] } }
          ]
        }
      };

      var actual = query_obj.body.query;
      expect(expected).toEqual(actual);
    });
  });
});
