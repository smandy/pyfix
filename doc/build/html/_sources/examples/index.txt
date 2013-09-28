.. _tut-examples:

****************
Interactive Use
****************

.. _tut-interactive:


Interactive Interpreter
=======================

One of the best ways of becoming familiar with the hierarchy is to use the interactive interpreter.

For example::

  >>> from pyfix.fix.FIXSpec import parseSpecification
  >>> fix = parseSpecification('FIX.4.2')
  Generating classes for fix fields ...
  Generating message content classes ...
  >>> fix.ExecutionReport
  <class 'pyfix.fix.FIXSpec.ExecutionReport'>
  >>> fix.ExecutionReport.mandatoryFields
  [Field(StandardHeader), Field(OrderID), Field(ExecID), Field(ExecTransType),   Field(ExecType), Field(OrdStatus), Field(Symbol), Field(Side), Field(LeavesQty),   Field(CumQty), Field(AvgPx), Field(StandardTrailer)]
  >>> 



