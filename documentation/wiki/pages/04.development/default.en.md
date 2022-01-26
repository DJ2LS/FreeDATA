---
title: Development
---

[flow]
st=>start: Start plugin
e=>end: End
op1=>operation: Development|success
sub1=>subroutine: Add features|success
cond=>condition: It is cool?|invalid
io=>inputoutput: Update for users|calm

st->op1->cond
cond(yes)->io->e
cond(no)->sub1(right)->op1
[/flow]