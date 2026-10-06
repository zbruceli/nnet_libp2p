#!/bin/sh
# Steady-state unicast: 90 s of identical traffic first, so (almost) every pair already has a connection.
cd "$(dirname "$0")"
for n in 128 256; do
  ./bench-libp2p -impl libp2p-direct -n $n -load 5000 -dur 20s -settle 45s -warm 90s -label libp2p-direct-warm >> results.jsonl
  ./bench-nnet  -impl nnet-relay    -n $n -load 5000 -dur 20s -settle 45s -warm 90s -label nnet-relay-warm >> results.jsonl
done
echo WARM-DONE
