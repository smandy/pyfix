.. _tut-tests:  .. _tut-interactive:  

**************** 
Tests
****************  

Description
===========

Tracking down corner cases associated with keeping FIX sessions in sequence during disconnects/network interruptions would have been difficult without a test suite.

In the twisted environment, due to the asynchronous nature of most tasts, having unit tests that run from start to completion doesn't complement the twisted model very well, for that reason twisted has its own test runner, ``trial`` which allows the test case to return a twisted ``Deferred``. The test then continues running until either the test code calls the deferred that it retuned, or a timeout period ends.


testAll.py
==========

This test gathers the test suites created by all other tests and runs each in turn::

     trial -e testAll.py

will run the whole test suite.



testFIXParser.py
================

The PyFIX parser, to work well with the asynchronous nature of twisted, is largely asynchronous. The parser is created with a specification object and a callback function. The parses is then fed bytes in arbitrary sized units, then when it believes it has assembled a complete FIX message it fires its callback.

The FIX specification recommends that any parser implementation should be able to decode FIX message that are received in fragments, so various tests are performed to ensure that the parser can deal with huge, tiny ( i.e one byte at a time ), and fragmented flow.


testFIXSession.py
=================

A few tests use this script as the core of their functionality. This script creates an acceptor session and immediately connects to the port opened up by that acceptor. The application can then send/receive messages from either of the sessions to test various conditions. In this case, the test is a simple logon/logout test, as well as testing the case where there is an acceptor or initiator sequence number gap. The app waits until the sessions have completely recovered and logs them out. 

The application keeps track of the 'state' of each session, ensuring that the sequence of state changes undergone by each session is in the sequence expected.


testFIXSpec.py
==============

Largely sanity checks to ensure that the field classes can re-generate messages that they have themselves parsed up.


testRejects.py
==============

This is based on ``testFIXSession.py``. Tests various types of message rejects Integrity checks and Business rejects.

- Ensure that sessions properly reject messages where the business logic is incorrect ( missing fields, inappropriate fields etc).
- Ensure that sessions ignore messages that don't pass basic integrity checks ( if body length or checksum on a message are incorrect the spec states that such messages should be ignored with no further action taken ).

testIntermittentGaps.py
=======================

This important test ensures that the system can correctly handle sequence number gaps and can correctly resequence in the event of message losses.

The initiating session will send a flurry of orders to the accptor, but for certain message will persist but not send the messages. The acceptor will then issue appropriate resend requests to the initiator in order to get back in sequence. The acceptors application object will keep track of the order messages it has been delivered and tests that the original stream of orders are delivered in order without gaps or duplications.

One case also deals with the case where the order is not even persisted, such that the resend request prompts a sequence-reset gapfill instead of a duplicate message.

















