"""
This module implements the TTYPE telnet protocol as per
http://tintin.sourceforge.net/mtts/. It allows the server to ask the
client about its capabilities. If the client also supports TTYPE, it
will return with information such as its name, if it supports colour
etc. If the client does not support TTYPE, this will be ignored.

All data will be stored on the protocol's protocol_flags dictionary,
under the 'TTYPE' key.
"""

# telnet option codes
TTYPE =  chr(24)
IS = chr(0)
SEND = chr(1)

# terminal capabilities and their codes
MTTS = [(128,'PROXY'), 
        (64, 'SCREEN READER'), 
        (32, 'OSC COLOR PALETTE'), 
        (16, 'MOUSE TRACKING'), 
        (8, '256 COLORS'), 
        (4, 'UTF-8'),
        (2, 'VT100'),
        (1, 'ANSI')]

class Ttype(object):
    """
    Handles ttype negotiations. Called and initiated by the 
    telnet protocol.
    """
    def __init__(self, protocol):
        """
        initialize ttype by storing protocol on ourselves and calling
        the client to see if it supporst ttype.

        the ttype_step indicates how far in the data retrieval we've
        gotten.
        """
        self.ttype_step = 0 
        self.protocol = protocol
        self.protocol.protocol_flags['TTYPE'] = {}

        # setup protocol to handle ttype initialization and negotiation
        self.protocol.negotiationMap[TTYPE] = self.negotiate_ttype                
        # ask if client will ttype, connect callback if it does.
        self.protocol.will(TTYPE).addCallbacks(self.negotiate_ttype, self.no_ttype)

    def no_ttype(self, option):
        """
        Callback if ttype is not supported by client. 
        """
        pass

    def negotiate_ttype(self, option):
        """
        Handles negotiation of the ttype protocol once the 
        client has confirmed that it supports the ttype 
        protocol.  

        The negotiation proceeds in several steps, each returning a
        certain piece of information about the client. All data is
        stored on protocol.protocol_flags under the TTYPE key.
        """

        self.ttype_step += 1

        if self.ttype_step == 1: 
            # set up info storage and initialize subnegotiation     
            self.protocol.requestNegotiation(TTYPE, SEND)
        else:
            # receive data 
            option = "".join(option).lstrip(IS)
            if self.ttype_step == 2:
                self.protocol.protocol_flags['TTYPE']['CLIENTNAME'] = option
                self.protocol.requestNegotiation(TTYPE, SEND)
            elif self.ttype_step == 3:
                self.protocol.protocol_flags['TTYPE']['TERM'] = option
                self.protocol.requestNegotiation(TTYPE, SEND)
            elif self.ttype_step == 4 and option.startswith('MTTS'):                
                option = int(option.strip('MTTS '))
                self.protocol.protocol_flags['TTYPE']['MTTS'] = option                
                for codenum, standard in MTTS: 
                    if option == 0:
                        break 
                    status = option % codenum < option
                    self.protocol.protocol_flags['TTYPE'][standard] = status
                    if status: 
                        option = option % codenum
            #print "ttype results:", self.protocol.protocol_flags['TTYPE']
            