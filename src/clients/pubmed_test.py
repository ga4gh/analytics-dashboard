import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from requests.exceptions import RequestException, HTTPError, ConnectionError

from src.clients.pubmed import Pubmed
from src.models.article import Article, Status
from src.models.author import Author


class TestPubmedClient:

    @pytest.fixture
    def pubmed_client(self):
        return Pubmed(base_url="https://test.pubmed.org", api_key="test_key")

    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.status_code = 200
        mock.raise_for_status = Mock()
        return mock

    def test_init(self):
        base_url = "https://test.pubmed.com"
        api_key = "test_key"
        client = Pubmed(base_url, api_key)
        assert client.base_url == base_url
        assert client.api_key == api_key

    @pytest.mark.parametrize("db,term,retmode,retmax,expected_term,returned_id_list", [
        ("pubmed", "ga4gh", "json", 20, "ga4gh[tw]", ["12345", "67890"]),
        ("pmc", "ga4gh beacon", "json", 50, "ga4gh beacon[tw]", ["12345", "67890"]),
        ("pubmed", "ga4gh", "xml", 10, "ga4gh[tw]", ["12345", "67890"]),
        ("pubmed", "ga4gh", "xml", 10, "ga4gh[tw]", []),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_uids_success(self, mock_get, pubmed_client, mock_response, db, term, retmode, retmax, expected_term, returned_id_list):
        mock_response.json.return_value = {
            "esearchresult": {
                "count": len(returned_id_list),
                "idlist": returned_id_list
            }
        }
        mock_get.return_value = mock_response

        result = pubmed_client.get_uids(db, term, retmode, retmax)

        assert result == returned_id_list
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert db == str(kwargs['params']['db'])
        assert retmode == str(kwargs['params']['retmode'])
        assert pubmed_client.api_key == str(kwargs['params']['api_key'])
        assert expected_term == str(kwargs['params']['term'])
        assert '0' == str(kwargs['params']['retstart'])
        assert str(retmax) == str(kwargs['params']['retmax'])
        assert 'analytics-dashboard' == str(kwargs['params']['tool'])

    @patch('src.clients.pubmed.requests.get')
    def test_get_uids_multiple_calls(self, mock_get, pubmed_client):
        responses = [
            Mock(status_code=200, json=lambda: {
                "esearchresult": {
                    "count": "5",
                    "idlist": ["id1", "id2"]
                }
            }),
            Mock(status_code=200, json=lambda: {
                "esearchresult": {
                    "count": "5",
                    "idlist": ["id3", "id4"]
                }
            }),
            Mock(status_code=200, json=lambda: {
                "esearchresult": {
                    "count": "5", 
                    "idlist": ["id5"]
                }
            })
        ]
        
        for response in responses:
            response.raise_for_status = Mock()
        
        mock_get.side_effect = responses

        result = pubmed_client.get_uids("pubmed", "ga4gh", retmax=2)

        assert mock_get.call_count == 3
        assert result == ["id1", "id2", "id3", "id4", "id5"]
        
        call_args_list = mock_get.call_args_list
        assert call_args_list[0][1]['params']['retstart'] == 0 
        assert call_args_list[1][1]['params']['retstart'] == 2 
        assert call_args_list[2][1]['params']['retstart'] == 4 

    @pytest.mark.parametrize("status_code,error_message", [
        (404, "404 Not Found"),
        (500, "500 Internal Server Error"),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_uids_http_errors(self, mock_get, pubmed_client, status_code, error_message):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.raise_for_status.side_effect = HTTPError(error_message)
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError) as exc_info:
            pubmed_client.get_uids("pubmed", "ga4gh")
        
        assert error_message == str(exc_info.value)

    @pytest.mark.parametrize("ids_count,batch_size,expected_calls", [
        (50, 200, 1),
        (250, 100, 3),
        (300, 200, 2),
        (10, 50, 1),
        (0, 200, 0),
        (1, 5, 1),
        (100, 250, 1),
        (500, 200, 3),
        (200, 200, 1),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_article_summaries_batch_processing(self, mock_get, pubmed_client, ids_count, batch_size, expected_calls):
        ids = [f"id_{i}" for i in range(ids_count)]
        
        if expected_calls == 0:
            result = pubmed_client.get_article_summaries("pubmed", ids, batch_size=batch_size)
            assert result == []
            assert mock_get.call_count == 0
            return
                
        def create_mock_response(call_number):
            batch_start = batch_size * call_number
            batch_end = batch_start + batch_size if batch_start + batch_size <= ids_count else batch_start + abs(ids_count - batch_start)
            batch_articles = {}
            print(call_number, batch_start, batch_end)
            for i in range(batch_start, batch_end):
                article_id = f"id_{i}"
                batch_articles[article_id] = {
                    "title": f"Test Article {i}",
                    "fulljournalname": f"Test Journal {i}",
                    "uid": article_id,
                    "articleids": [{"idtype": "doi", "value": f"10.1234/test_{i}"}],
                    "pubdate": "2023",
                    "epubdate": ""
                }
            
            response = Mock(status_code=200)
            response.raise_for_status = Mock()
            response.json.return_value = {"result": batch_articles}
            return response
        
        if expected_calls == 1:
            mock_get.return_value = create_mock_response(0)
        else:
            mock_responses = [create_mock_response(i) for i in range(expected_calls)]
            mock_get.side_effect = mock_responses

        result = pubmed_client.get_article_summaries("pubmed", ids, batch_size=batch_size)

        assert mock_get.call_count == expected_calls
        
        assert isinstance(result, list)
        
        assert len(result) == ids_count
        
        for i, article in enumerate(result):
            assert isinstance(article, Article)
            assert article.title == f"Test Article {i}"
            assert article.journal == f"Test Journal {i}"
            assert article.source_id == f"id_{i}"
            assert article.doi == f"10.1234/test_{i}"

    @pytest.mark.parametrize("db,retmode,ids", [
        ("pubmed", "json", ["12345", "67890"]),
        ("pmc", "json", ["PMC123", "PMC456"]),
        ("pubmed", "xml", ["id1", "id2", "id3"]),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_article_summaries_different_databases(self, mock_get, pubmed_client, db, retmode, ids):
        mock_response = Mock(status_code=200)
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "result": {
                ids[0]: {
                    "title": f"Article from {db}",
                    "fulljournalname": f"{db.upper()} Journal",
                    "uid": ids[0],
                    "articleids": [],
                    "pubdate": "2023",
                    "epubdate": ""
                }
            }
        }
        mock_get.return_value = mock_response

        result = pubmed_client.get_article_summaries(db, ids, retmode=retmode)

        assert mock_get.call_count == 1
        assert len(result) >= 0
        
        call_args = mock_get.call_args
        assert call_args[1]['params']['db'] == db
        assert call_args[1]['params']['retmode'] == retmode
        assert call_args[1]['params']['id'] == ",".join(ids)

    @pytest.mark.parametrize("exception_type,exception_message", [
        (RequestException, "Network timeout"),
        (ValueError, "Invalid JSON response"),
        (KeyError, "Missing required field"),
        (TypeError, "Type conversion error"),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_article_summaries_exception_handling(self, mock_get, pubmed_client, exception_type, exception_message):
        ids = ["id1", "id2", "id3"]
        
        responses = [
            Mock(status_code=200, json=lambda: {
                "result": {
                    "id1": {
                        "title": "Success Article",
                        "fulljournalname": "Success Journal",
                        "uid": "id1",
                        "articleids": [],
                        "pubdate": "2023",
                        "epubdate": ""
                    }
                }
            }),
            exception_type(exception_message),
            Mock(status_code=200, json=lambda: {
                "result": {
                    "id3": {
                        "title": "Another Success Article",
                        "fulljournalname": "Another Journal",
                        "uid": "id3",
                        "articleids": [],
                        "pubdate": "2023",
                        "epubdate": ""
                    }
                }
            })
        ]
        responses[0].raise_for_status = Mock()
        responses[2].raise_for_status = Mock()
        mock_get.side_effect = responses

        result = pubmed_client.get_article_summaries("pubmed", ids, batch_size=1)
        
        assert isinstance(result, list)
        assert mock_get.call_count == 3
        assert len(result) == 2
        assert result[0].title == "Success Article"
        assert result[1].title == "Another Success Article"

    @pytest.mark.parametrize("db,retmode,expected_parser", [
        ("pubmed", "xml", "parse_pubmed_article"),
        ("pmc", "xml", "parse_pmc_article"),
    ])
    @patch('src.clients.pubmed.requests.get')
    @patch('src.clients.pubmed.xmltodict.parse')
    def test_get_detailed_article_info_different_dbs(self, mock_xmlparse, mock_get, pubmed_client, mock_response, db, retmode, expected_parser):
        mock_response.text = "<xml>test</xml>"
        mock_get.return_value = mock_response
        mock_xmlparse.return_value = {"test": "data"}

        with patch.object(pubmed_client, expected_parser, return_value={
            "abstract": "Test abstract",
            "authors": [],
            "status": "published",
            "link": "http://test.com",
        }):
            result = pubmed_client.get_detailed_article_info(db, "test_id", retmode)

        assert result is not None
        article, status = result
        assert isinstance(article, Article)
        assert article.abstract == "Test abstract"
        assert status == "published"
        assert article.status == Status.UNKNOWN

    @pytest.mark.parametrize("status_code,error_message", [
        (404, "404 Not Found"),
        (500, "500 Internal Server Error")
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_detailed_article_info_http_errors(self, mock_get, pubmed_client, status_code, error_message):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.raise_for_status.side_effect = HTTPError(error_message)
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError) as exc_info:
            pubmed_client.get_detailed_article_info("pubmed", "test_id")
        
        assert error_message == str(exc_info.value)

    @pytest.mark.parametrize("exception_type,exception_message", [
        (RequestException, "Network timeout"),
        (ConnectionError, "Connection failed"),
    ])
    @patch('src.clients.pubmed.requests.get')
    def test_get_detailed_article_info_request_exceptions(self, mock_get, pubmed_client, exception_type, exception_message):
        mock_get.side_effect = exception_type(exception_message)

        with pytest.raises(exception_type) as exc_info:
            pubmed_client.get_detailed_article_info("pubmed", "test_id")
        
        assert exception_message == str(exc_info.value)

    @pytest.mark.parametrize("db,malformed_xml", [
        ("pubmed", "<invalid>xml</broken>"),
        ("pmc", "<incomplete>"),
        ("pubmed", "not xml at all"),
        ("pmc", ""),
    ])
    @patch('src.clients.pubmed.requests.get')
    @patch('src.clients.pubmed.xmltodict.parse')
    def test_get_detailed_article_info_xml_parsing_errors(self, mock_xmlparse, mock_get, pubmed_client, db, malformed_xml):
        mock_response = Mock(status_code=200)
        mock_response.raise_for_status = Mock()
        mock_response.text = malformed_xml
        mock_get.return_value = mock_response
        
        mock_xmlparse.side_effect = Exception("XML parsing failed")

        with pytest.raises(Exception) as exc_info:
            pubmed_client.get_detailed_article_info(db, "test_id")
        
        assert "XML parsing failed" == str(exc_info.value)

    @pytest.mark.parametrize("db,xml_data", [
        ("pubmed", {"invalid": "structure"}),
        ("pmc", {"wrong": "format"}),
    ])
    @patch('src.clients.pubmed.requests.get')
    @patch('src.clients.pubmed.xmltodict.parse')
    def test_get_detailed_article_info_parsing_exception_handling(self, mock_xmlparse, mock_get, pubmed_client, db, xml_data):
        mock_response = Mock(status_code=200)
        mock_response.raise_for_status = Mock()
        mock_response.text = "<xml>test</xml>"
        mock_get.return_value = mock_response
        mock_xmlparse.return_value = xml_data

        result = pubmed_client.get_detailed_article_info(db, "test_id")

        assert result is not None
        article, status = result
        assert isinstance(article, Article)
        if db == "pubmed":
            assert article.abstract is None or article.abstract == ""
            assert article.authors == [] 
        else:
            assert article.abstract == ""
            assert article.authors == []

    @patch('src.clients.pubmed.requests.get')
    @patch('src.clients.pubmed.xmltodict.parse')
    def test_get_detailed_article_info_timeout_handling(self, mock_xmlparse, mock_get, pubmed_client):
        mock_get.side_effect = RequestException("Request timeout")

        with pytest.raises(RequestException) as exc_info:
            pubmed_client.get_detailed_article_info("pubmed", "test_id")
        
        assert "Request timeout" == str(exc_info.value)
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 120

    @pytest.mark.parametrize("db,author_data_scenario", [
        ("pubmed", "author_creation_fails"),
        ("pubmed", "malformed_author_data"),
        ("pmc", "author_creation_fails"),
        ("pmc", "malformed_pmc_author_data"),
    ])
    @patch('src.clients.pubmed.requests.get')
    @patch('src.clients.pubmed.xmltodict.parse')
    def test_get_detailed_article_info_author_parsing_failures(self, mock_xmlparse, mock_get, pubmed_client, db, author_data_scenario):
        mock_response = Mock(status_code=200)
        mock_response.raise_for_status = Mock()
        mock_response.text = "<xml>test</xml>"
        mock_get.return_value = mock_response

        if db == "pubmed":
            if author_data_scenario == "author_creation_fails":
                xml_data = {
                    "PubmedArticleSet": {
                        "PubmedArticle": {
                            "MedlineCitation": {
                                "Article": {
                                    "AuthorList": {
                                        "Author": [
                                            {"LastName": "Smith", "ForeName": "John"},
                                            {"LastName": None, "ForeName": None}  
                                        ]
                                    }
                                }
                            },
                            "PubmedData": {"PublicationStatus": "published"}
                        }
                    }
                }
            else: 
                xml_data = {
                    "PubmedArticleSet": {
                        "PubmedArticle": {
                            "MedlineCitation": {
                                "Article": {
                                    "AuthorList": {
                                        "Author": "invalid_string_instead_of_dict" 
                                    }
                                }
                            },
                            "PubmedData": {"PublicationStatus": "published"}
                        }
                    }
                }
        else:  
            if author_data_scenario == "author_creation_fails":
                xml_data = {
                    "pmc-articleset": {
                        "article": {
                            "front": {
                                "article-meta": {
                                    "contrib-group": {
                                        "contrib": [
                                            {
                                                "@contrib-type": "author",
                                                "name": {
                                                    "given-names": {"#text": "John"},
                                                    "surname": "Smith"
                                                }
                                            },
                                            {
                                                "@contrib-type": "author",
                                                "name": None
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            else:
                xml_data = {
                    "pmc-articleset": {
                        "article": {
                            "front": {
                                "article-meta": {
                                    "contrib-group": {
                                        "contrib": "invalid_string_instead_of_dict"  # Invalid structure
                                    }
                                }
                            }
                        }
                    }
                }

        mock_xmlparse.return_value = xml_data

        if author_data_scenario in ["malformed_author_data", "malformed_pmc_author_data", "author_creation_fails"]:
            from pydantic import ValidationError
            
            if db == "pubmed" and author_data_scenario == "author_creation_fails":
                result = pubmed_client.get_detailed_article_info(db, "test_id")

                assert result is not None
                article, status = result
                assert isinstance(article, Article)
                
                assert isinstance(article.authors, list)
                for author in article.authors:
                    assert isinstance(author, Author)
                    assert author.name != "" 
            else:
                with pytest.raises(ValidationError) as exc_info:
                    pubmed_client.get_detailed_article_info(db, "test_id")
                
                assert "authors" in str(exc_info.value)
                assert "Input should be a valid list" in str(exc_info.value)
