# take name of wav file from stdin and dump formant table to stdout
form File
sentence filename
positive maxformant 5500
real winlen 0.025
positive preemph 50
endform
Read from file... 'filename$'
To Formant (burg)... 0.01 5 'maxformant' 'winlen' 'preemph'
List... no yes 6 no 3 no 3 no
exit
