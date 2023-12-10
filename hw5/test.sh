#!/bin/bash

python3 bwt_huffman.py -c -i sample.txt -o s.huf
python3 bwt_huffman.py -d -i s.huf -o sample_out.txt
diff sample.txt sample_out.txt && echo "✔️  SUCCESS: sample.txt" || echo "❌ ERROR: Files are different!"

python3 bwt_huffman.py -c -b -i office_hours.bmp -o o.huf
python3 bwt_huffman.py -d -b -i o.huf -o office_hours_output.bmp
diff office_hours.bmp office_hours_output.bmp && echo "✔️  SUCCESS: office_hours.bmp" || echo "❌   ERROR: Files are different!"
