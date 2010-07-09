# 
# pubsub.py
# 
# Copyright (C) 2010 Antoine Mercadal <antoine.mercadal@inframonde.eu>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from utils import *
import xmpp
import types


XMPP_PUBSUB_VAR_TITLE                       = "pubsub#title"
XMPP_PUBSUB_VAR_DELIVER_NOTIFICATION        = "pubsub#deliver_notifications"
XMPP_PUBSUB_VAR_DELIVER_PAYLOADS            = "pubsub#deliver_payloads"
XMPP_PUBSUB_VAR_PERSIST_ITEMS               = "pubsub#persist_items"
XMPP_PUBSUB_VAR_MAX_ITEMS                   = "pubsub#max_items"
XMPP_PUBSUB_VAR_ITEM_EXPIRE                 = "pubsub#item_expire"
XMPP_PUBSUB_VAR_ACCESS_MODEL                = "pubsub#access_model"
XMPP_PUBSUB_VAR_ROSTER_GROUP_ALLOWED        = "pubsub#roster_groups_allowed"
XMPP_PUBSUB_VAR_PUBLISH_MODEL               = "pubsub#publish_model"
XMPP_PUBSUB_VAR_PURGE_OFFLINE               = "pubsub#purge_offline"
XMPP_PUBSUB_VAR_SEND_LAST_PUBLISHED_ITEM    = "pubsub#send_last_published_item"
XMPP_PUBSUB_VAR_PRESENCE_BASED_DELIVERY     = "pubsub#presence_based_delivery"
XMPP_PUBSUB_VAR_NOTIFICATION_TYPE           = "pubsub#notification_type"
XMPP_PUBSUB_VAR_NOTIFY_CONFIG               = "pubsub#notify_config"
XMPP_PUBSUB_VAR_NOTIFY_DELETE               = "pubsub#notify_delete"
XMPP_PUBSUB_VAR_NOTIFY_RECTRACT             = "pubsub#notify_retract"
XMPP_PUBSUB_VAR_NOTIFY_SUB                  = "pubsub#notify_sub"
XMPP_PUBSUB_VAR_MAX_PAYLOAD_SIZE            = "pubsub#max_payload_size"
XMPP_PUBSUB_VAR_TYPE                        = "pubsub#type"
XMPP_PUBSUB_VAR_BODY_XSLT                   = "pubsub#body_xslt"

XMPP_PUBSUB_VAR_ACCESS_MODEL_OPEN           = "open"
XMPP_PUBSUB_VAR_ACCESS_MODEL_ROSTER         = "roster"
XMPP_PUBSUB_VAR_ACCESS_MODEL_AUTHORIZE      = "authorize"
XMPP_PUBSUB_VAR_ACCESS_MODEL_WHITELIST      = "whitelist"


class TNPubSubNode:
    
    def __init__(self, xmppclient, pubsubserver, nodename):
        self.xmppclient     = xmppclient
        self.pubsubserver   = pubsubserver
        self.nodename       = nodename
        self.node           = None
    
    def get(self):
        """
        get the current pubsub node. If not already recovered, ask to server
        """
        if self.node: return self.node
        try:
            disco_pubsubs   = xmpp.Iq(typ="get", to=self.pubsubserver, queryNS=xmpp.protocol.NS_DISCO_ITEMS)
            resp            = self.xmppclient.SendAndWaitForResponse(disco_pubsubs)
            
            if resp.getType() == "result":
                items = resp.getTag("query").getTags("item")
                for item in items:
                    if item.getAttr("node") == self.nodename:
                        self.node = item
                        log.info("PUBSUB: recovered node")
                        break
            
            return self.node
        
        except Exception as ex:
            log.error("PUBSUB: can't get node %s : %s" % (self.nodename, str(ex)))
            return self.node
    
    
    def create(self):
        """
        create node on server if not exists
        """
        log.info("PUBSUB: trying to create pubsub node %s" % self.nodename)
        
        if self.node: raise Exception("PUBSUB: node %s already exists" % self.nodename)
        
        try:
            iq      = xmpp.Iq(typ="set", to=self.pubsubserver)
            
            iq.addChild(name="pubsub", namespace=xmpp.protocol.NS_PUBSUB).addChild(name="create", attrs={"node": self.nodename})
            resp = self.xmppclient.SendAndWaitForResponse(iq)
            if resp.getType() == "result": 
                log.info("PUBSUB: pubsub node %s has been created" % self.nodename)
                self.get()
            else:
                log.error("PUBSUB: can't configure pubsub: %s" % str(resp))
        except Exception as ex:
            log.error("PUBSUB: unable to create pubsub node: %s" % str(ex))
    
    
    def delete(self, nowait=False):
        """delete the node from server if exists"""
        
        if not self.node: raise Exception("PUBSUB: node %s doesn't exists" % self.nodename)
        
        try:
            iq      = xmpp.Iq(typ="set", to=self.pubsubserver)
            
            iq.addChild(name="pubsub", namespace=xmpp.protocol.NS_PUBSUB + "#owner").addChild(name="delete", attrs={"node": self.nodename})
            
            if nowait:
                self.xmppclient.send(iq)
                return
            else:
                resp = self.xmppclient.SendAndWaitForResponse(iq)
                if resp.getType() == "result": 
                    log.info("PUBSUB: pubsub node %s has been deleted" % self.nodename)
                else:
                    log.error("PUBSUB: can't delete pubsub: %s" % str(resp))
        except Exception as ex:
            log.error("PUBSUB: unable to delete pubsub node: %s" % str(ex))
    
    
    def configure(self, options):
        """configure the node"""
        if not self.node: raise Exception("PUBSUB: node %s doesn't exists" % self.nodename)
        
        
        # ask conf of server
        # iq          = xmpp.Iq(typ="get", to=self.pubsubserver)
        # pubsub      = iq.addChild("pubsub", namespace=xmpp.protocol.NS_PUBSUB + "#owner")
        # configure   = pubsub.addChild("configure", attrs={"node": self.nodename})
        # resp = self.xmppclient.SendAndWaitForResponse(iq)
        # print "\n\n" + str(resp) + "\n\n"
        
        iq          = xmpp.Iq(typ="set", to=self.pubsubserver)
        pubsub      = iq.addChild("pubsub", namespace=xmpp.protocol.NS_PUBSUB + "#owner")
        configure   = pubsub.addChild("configure", attrs={"node": self.nodename})
        x           = configure.addChild("x", namespace=xmpp.protocol.NS_DATA, attrs={"type": "submit"})
        
        x.addChild("field", attrs={"var": "FORM_TYPE", "type": "hidden"}).addChild("value").setData("http://jabber.org/protocol/pubsub#node_config")
        
        for key, value in options.items():
            field = x.addChild("field", attrs={"var": key})
            if type(value) == types.ListType:
                for v in value:
                    field.addChild("value").setData(v)
            else:
                field.addChild("value").setData(str(value))
        #print "\n\n" + str(iq) + "\n\n"
        try:
            resp = self.xmppclient.SendAndWaitForResponse(iq)
            if resp.getType() == "result": 
                log.info("PUBSUB: pubsub node %s has been configured" % self.nodename)
            else:
                log.error("PUBSUB: can't configure pubsub: %s" % str(resp))
        except Exception as ex:
            log.error("PUBSUB: unable to configure pubsub node: %s" % str(ex))
    
    
    def add_item(self, itemcontentnode, callback=None):
        """
        add a leaf item xmpp.node to the node and will trigger callback if any
        on server answer
        """
        if not self.node: raise Exception("PUBSUB: node %s doesn't exists" % self.nodename)
        
        iq          = xmpp.Iq(typ="set", to=self.pubsubserver)
        pubsub      = iq.addChild("pubsub", namespace=xmpp.protocol.NS_PUBSUB)
        publish     = pubsub.addChild("publish", attrs={"node": self.nodename})
        item        = publish.addChild("item")
        
        item.addChild(node=itemcontentnode)
        
        #print "\n\n" + str(iq) + "\n\n"
        resp = self.xmppclient.SendAndCallForResponse(iq, func=self.did_publish_item, args={"callback": callback})
        
    def did_publish_item(self, conn, response, callback):
        """
        triggered on response
        """
        log.debug("PUBSUB: publish done. Answer is : %s" % str(response.getType()))
        if callback: callback(response)


    