.. _tut-examples:  .. _tut-interactive:  

**************** 
Description
****************  

Introduction 
======================= 

pyFIX is an implementation of the Financial Implementation eXchange
(FIX) protocol. It utilises python's 'Twisted' event processing
framework to handle TCP/IP connectivity and session management. It
supports both initiator and acceptor type sessions.

The system supports an arbitrary number of outgoing and incoming
connections. Each 'acceptor' session is associated with only one
listening port. However any number of listening ports can be
opened. This may be useful in multi-homed setups. Due to twisted's
asynchronous processing model the number of sessions can scale
reasonably well.

Background
==========

This code began as an attempt to learn to use metaclasses properly
during a very cold snap in London when there was little that could be
done outside once the novelty of making snowmen had worn off.

From experiments with metaclasses it seemed natural that the FIX
Specification would lend itself quite nicely to being dynamically
rendered *on-the-fly* as a class hierarchy.

Once that was done it seemed like a natural next step to see if it was
possible to generate a FIX message which would pass validation by a
FIX parser.

Moving on from there it seemed like a next obvious step to see if the
messages could be sent down a socket so as to convince a real FIX
Server into accepting a connection and heartbeating sufficiently with
it, such that it wouldn't close the connection.

By this time it was evident that enough had been done that it would be
a shame to not go the whole hog and provide a reasonably complete
protocol implementation.

Features 
=========

Implementation has following features.

- Dynamic Creation of classes based on FIX Specification XML 

  Message and Field classes are created on startup according to the spec using python's class factory logic. 

- Type safe fields

  The FIX Field classes are aware of their types and will fail to
  validate if a field is created using a value that cannot be
  converted to the required type.

- Dynamic Session creation

  Sessions can be added to the server programattically during the session.

- Multicast discovery

  A simple multicast discovery library is included which allows
  Session managers to anounce their presence on a network. This
  functionality is useful for guis to locate remote sessions managers,
  as in the more complex use cases there may be several session
  managers running on different hosts at the same time.

- Benefits from Twisted

  Being based on twisted all the benefits of writing an app using the
  twisted framework are available, such as -

  - Programattic 'remote' interface to the server.
    
    Examples include a pyglet based session viewer example is included
    which shows conecting to an instance with the PB protocol. Also an
    FTP/FIX bridge is in included which demonstrates how it it
    possible to FTP a file info the server which will then be
    translated to FIX orders, the executions for which are made
    available as downloadable 'psuedo-files' made available using the
    twited FTP server.

Dependencies 
=============  

   In general have tried to keep dependencies to a minimum, and stuck
   to using modules in the standard library where available. Cases
   where have had to veer outside the standard library have tried to
   stick with modules that can be installed with easy_install. With
   the exception of wxPython the remainder of the dependencies have
   all been tested to install cleanly on top of a fresh python
   installation using easy_install.

- Twisted 8.2.0

  The code was developed using the ( at the time ) latest version of Twisted.

- Python 2.5/2.6

  Pyfix has been tested on python2.5 and python2.6. the core of the
  parser depends on the relatively new (and fast!) string.partition
  method to parse FIX messages.

- Berkeley DB. 

  Used for persistence of FIX messages. The RECNO format is used since
  it supports integer keys and lends itself nicely to storing session
  state. It should be straightforward to implement a version that uses
  any of the anydbm variants, although this would require switching to
  string keys. For now I'll assume that the bsddb or bsddb3 modules
  are availbale ( or easily installable on the client machine).

- pyyaml

  Session config is based on yaml but the config objects can be
  created directly in python if preferred.

- pyglet

  Required by one of the gui examples.

- wxPython

  Required for the tabular message viewer application.

- PyCrypto ( Optional )

  Required by the manhols ssh server if the remote interpreter
  functionality is to be used.

- pyOpenSSL ( Optional )

  Required for SSL encrypted links

  

