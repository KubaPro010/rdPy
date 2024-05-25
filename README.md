# rdPy
rdPy is a python RDS encoder, encoder not modulator you can't use it in your setup just like that, it is a proof-of-concept program

what libs are used? are you asking what libs are used? time can be used in the example, but the generation itself only requires enum for af, enum is a python [stdlib](https://docs.python.org/3/library/enum.html)

There is a package version on https://flerken.zapto.org:1115/kuba/librds, clone it and run `pip install .`
# Features
rdPy has a built in Group Sequencer, Group Interfacer (to prepare the text and segments for group gen) a print function which will print in a format that you can pass into redsea or output to a .spy file to be read by rds spy, Alternative Frequency (FM, LF, MF, RBDS MF), also recently a bit stream was added, that can example can be modulated with [pydemod](https://github.com/ChristopheJacquet/Pydemod) or a another lib/app
# Groups
rdPy can encode these groups:<br>
  -Basic group (basics for every group such as the pi code, tp and pty<br>
  -PS (with toggable ms, ta, changable di and possibility of setting block 2 for af, you don't want af? just use the 0B group or just dont pass in block2 into the ps func)<br>
  -RT (with toggable AB)<br>
  -PTYN<br>
  -ECC<br>
  -LIC<br>
  -?CT (probably not working)<br>
# Code
the main.py file contains the code for RDS itself and a example use-case at the end


**Note** that the example use-case and the charset to run requires atleast python 3.10 with its use of `match`
