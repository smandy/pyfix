#!/usr/bin/env sh

echo "Starting sinks..."
python sinks.py > sink.log 2>&1 &

sleep 10

echo "Starting mux..."
python mux.py > mux.log 2>&1 &
# I think the muxPerspective was made obsolete bevause mux.py can do both.
# python ../pyglet/muxPerspective.py > mux.log 2>&1 &

sleep 10

echo "Starting sources..."
python sources.py > source.log 2>&1 &

