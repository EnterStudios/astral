from nose.tools import eq_, ok_
from tornado.httpclient import HTTPRequest
import json
import mockito

from astral.api.tests import BaseTest
from astral.api.client import Tickets
from astral.models import Ticket, Node, session
from astral.models.tests.factories import (StreamFactory, NodeFactory,
        ThisNodeFactory, TicketFactory)

class TicketsHandlerTest(BaseTest):
    def setUp(self):
        super(TicketsHandlerTest, self).setUp()
        ThisNodeFactory()
        session.commit()

    def test_create(self):
        stream = StreamFactory()
        node = NodeFactory()
        self.http_client.fetch(HTTPRequest(
            self.get_url(stream.tickets_url()), 'POST',
            body=json.dumps({'destination_uuid': node.uuid})), self.stop)
        response = self.wait()
        eq_(response.code, 200)
        result = json.loads(response.body)
        ok_('stream' in result)
        eq_(result['stream']['id'], stream.id)
        eq_(result['stream']['name'], stream.name)
        ticket = Ticket.query.first()
        eq_(ticket.stream, stream)
        eq_(ticket.destination, node)

    def test_bad_destination(self):
        stream = StreamFactory()
        self.http_client.fetch(HTTPRequest(
            self.get_url(stream.tickets_url()), 'POST',
            body=json.dumps({'destination_uuid': 'foo'})), self.stop)
        response = self.wait()
        eq_(response.code, 404)

    def test_trigger_locally(self):
        stream = StreamFactory(source=Node.me())
        self.http_client.fetch(HTTPRequest(
            self.get_url(stream.tickets_url()), 'POST', body=''),
            self.stop)
        response = self.wait()
        eq_(response.code, 200)
        result = json.loads(response.body)
        ok_('stream' in result)
        eq_(result['stream']['id'], stream.id)
        eq_(result['stream']['name'], stream.name)
        ticket = Ticket.query.first()
        eq_(ticket.stream, stream)
        eq_(ticket.destination, Node.me())

    def test_create_twice_locally(self):
        stream = StreamFactory(source=Node.me())
        TicketFactory(stream=stream, destination=Node.me())
        self.http_client.fetch(HTTPRequest(
            self.get_url(stream.tickets_url()), 'POST', body=''),
            self.stop)
        response = self.wait()
        eq_(response.code, 200)

    def test_already_streaming(self):
        stream = StreamFactory(source=Node.me())
        TicketFactory(stream=stream, source=Node.me())
        self.http_client.fetch(HTTPRequest(
            self.get_url(stream.tickets_url()), 'POST', body=''),
            self.stop)
        response = self.wait()
        eq_(response.code, 200)

    def test_remote_source(self):
        mockito.when(Tickets).create(mockito.any(),
                destination_uuid=mockito.any()).thenReturn(True)
        stream = StreamFactory()
        tickets_before = Ticket.query.count()
        self.http_client.fetch(HTTPRequest(self.get_url(stream.tickets_url()),
            'POST', body=''), self.stop)
        response = self.wait()
        eq_(response.code, 200)
        eq_(Ticket.query.count(), tickets_before + 2)

    def test_none_available(self):
        mockito.when(Tickets).create(mockito.any(),
                destination_uuid=mockito.any()).thenReturn(False)
        stream = StreamFactory()
        tickets_before = Ticket.query.count()
        self.http_client.fetch(HTTPRequest(self.get_url(stream.tickets_url()),
            'POST', body=''), self.stop)
        response = self.wait()
        eq_(response.code, 412)
        eq_(Ticket.query.count(), tickets_before)

class TicketsListHandlerTest(BaseTest):
    def setUp(self):
        super(TicketsListHandlerTest, self).setUp()
        [TicketFactory for _ in range(3)]

    def test_get_tickets(self):
        response = self.fetch('/tickets')
        eq_(response.code, 200)
        result = json.loads(response.body)
        ok_('tickets' in result)
        for ticket in result['tickets']:
            source = Node.get_by(uuid=ticket['source_uuid'])
            destination = Node.get_by(uuid=ticket['destination_uuid'])
            ok_(Ticket.get_by(stream=ticket['stream_id'],
                source=source, destination=destination))

