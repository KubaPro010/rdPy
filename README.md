# rdPy
rdPy is a python RDS encoder, encoder not modulator you can't use it in your setup just like that, it is a proof-of-concept program
# Features
rdPy has a built in Group Sequencer, Group Interfacer (to prepare the text and segments for group gen) a print function which will print in a format that you can pass into redsea or output to a .spy file to be read by rds spy, Alternative Frequency (FM, LF, MF, RBDS MF)
# Groups
rdPy can encode these groups:
  -Basic group (basics for every group such as the pi code, tp and pty
  -PS (with toggable ms, ta, changable di and possibility of setting block 2 for af)
  -RT (with toggable AB)
  -PTYN
  -ECC
  -LIC
  -?CT (probably not working)
# Code
the main.py file contains the code for RDS itself and a example use-case at the end
