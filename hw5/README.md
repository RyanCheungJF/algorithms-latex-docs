## Huffman Encoding

### Create venv
`python -m venv ./<name_of_venv>`

### Activate venv in CMD
`venv\Scripts\activate.bat`

### Kill venv
`deactivate`


notes:

huffman encoding: 
attach weights and probabilities to each letter, then form a tree where lower probabilities are at the bottom
encode the left and right branches with 0 and 1s such that we have a unique representation for each letter

bwt:
we can form a bwt through forming the matrix, then sorting it by the first letter
taking the last letter in order is the bwt, where similar letters tend to be together

ibwt:
we can take the bwt and form the normal word
we do this by taking the last column of the bwm (or the bwt itself), sort it to get back the first column
then move the last column back before the first column so now we have 2 cols at start
then sort the two columns again and keep re-using the bwt to repeat it ( we don't need the bwm)
(can potentially do the index tracing?)