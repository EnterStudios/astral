from nose.tools import ok_, eq_, raises
import mockito
import restkit

from astral.models.node import Node
from astral.api.client import NodeAPI
from astral.api.tests import BaseTest


class NodeRTTTest(BaseTest):
    def setUp(self):
        super(NodeRTTTest, self).setUp()
        self.node = Node(ip_address='localhost', port='8000')

    @raises(restkit.RequestError)
    def test_update_rtt_error(self):
        mockito.when(NodeAPI).ping().thenRaise(restkit.RequestError())
        rtt = self.node.update_rtt()
        eq_(rtt, None)

    def test_update_rtt(self):
        mockito.when(NodeAPI).ping().thenReturn(42)
        eq_(self.node.rtt, None)
        rtt = self.node.update_rtt()
        eq_(rtt, 42)
        eq_(self.node.rtt, rtt)

    def test_weighted_rtt(self):
        mockito.when(NodeAPI).ping().thenReturn(10)
        self.node.rtt = 100
        rtt = self.node.update_rtt()
        ok_(rtt < 100)
        ok_(rtt > 10)


class NodeDownstreamTest(BaseTest):
    def setUp(self):
        super(NodeDownstreamTest, self).setUp()
        self.node = Node(ip_address='localhost', port='8000')

    @raises(restkit.RequestError)
    def test_update_downstream_error(self):
        mockito.when(NodeAPI).downstream_check().thenRaise(
                restkit.RequestError())
        downstream = self.node.update_downstream()
        eq_(downstream, None)

    def test_update_downstream(self):
        mockito.when(NodeAPI).downstream_check().thenReturn((100, 10.0))
        eq_(self.node.downstream, None)
        downstream = self.node.update_downstream()
        eq_(downstream, 100 / 10.0)
        eq_(self.node.downstream, downstream)

    def test_weighted_downstream(self):
        mockito.when(NodeAPI).downstream_check().thenReturn((100, 10.0))
        self.node.downstream = 100
        downstream = self.node.update_downstream()
        ok_(downstream < 100)
        ok_(downstream > 10)


class NodeUpstreamTest(BaseTest):
    def setUp(self):
        super(NodeUpstreamTest, self).setUp()
        self.node = Node(ip_address='localhost', port='8000')

    @raises(restkit.RequestError)
    def test_update_upstream_error(self):
        mockito.when(NodeAPI).upstream_check().thenRaise(
                restkit.RequestError())
        upstream = self.node.update_upstream()
        eq_(upstream, None)

    def test_update_upstream(self):
        mockito.when(NodeAPI).upstream_check().thenReturn((100, 10.0))
        eq_(self.node.upstream, None)
        upstream = self.node.update_upstream()
        eq_(upstream, 100 / 10.0)
        eq_(self.node.upstream, upstream)

    def test_weighted_upstream(self):
        mockito.when(NodeAPI).upstream_check().thenReturn((100, 10.0))
        self.node.upstream = 100
        upstream = self.node.update_upstream()
        ok_(upstream < 100)
        ok_(upstream > 10)