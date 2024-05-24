"""For the implementation of this, this was used:
    -https://stackoverflow.com/questions/5676646/how-can-i-fill-out-a-python-string-with-spaces
    -https://github.com/barteqcz/MicroRDS/blob/main/src/rds.c
    -https://github.com/barteqcz/MicroRDS/blob/main/src/lib.c (for af and the charset)
    -http://www.interactive-radio-system.com/docs/EN50067_RDS_Standard.pdf (for the mjd calculation and 0B)
this is mostly tested with RDS Spy and redsea
bash Commands used: /bin/python /home/kuba/rdsEncoder.py | redsea -h  /bin/python /home/kuba/rdsEncoder.py > test.spy , python3 rdsEncoder.py | redsea -i bits -R

Does it work? yes, excluding CT, i can't properly test it however it might be working if you just decode it properly"""

#AF
from enum import Enum, IntEnum
class AF_Codes(Enum):
    Filler = 205
    NoAF = 224
    NumAFSBase = 224 #same as no af
    LfMf_Follows = 250
class AF_Bands(Enum):
    FM = 0
    LF = 1
    MF = 2
    MF_RBDS = 3
class AlternativeFrequencyEntry:
    """This is a AF Entry which will be used by the AF Class"""
    af_freq = 0
    lenght = 1
    lfmf = False
    freq = 0
    band = IntEnum
    def __init__(self, band:IntEnum, frequency:float) -> None:
        self.freq = frequency
        self.band = band
        self.lfmf = band != AF_Bands.FM
        self.lenght = 2 if self.lfmf else 1
        match band:
            case AF_Bands.FM:
                self.af_freq = int((int(frequency*10)) - (87.5*10))
            case AF_Bands.LF:
                self.af_freq = int(int(frequency - 153.0)/9+1)
            case AF_Bands.MF:
                self.af_freq = int(int(frequency - 531.0)/9+16)
            case AF_Bands.MF_RBDS:
                self.af_freq = int(int(frequency - 540.0)/10+17)
    def __len__(self):
        return self.lenght
    def __repr__(self) -> str:
        return f"<AFEntry FREQ:{self.freq} BAND:{self.band.name} AF_FREQ:{self.af_freq} LEN:{self.lenght} LFMF:{self.lfmf}>"
class AlternativeFrequency:
    """This is a working Alterntive Frequency implementation that was tested on FM, LF, MF, RBDS MF
    however the rbds MF does have a problem, on rds mf 540 and 549 work but 550 doesnt, this is expected as 550 is not divisible by 9 as in europe am has a 9 khz step
    in the us however am has a 10 khz step 540 works as expected but 549 round to 540, as expected but 550 does the same?
    but im doing rbds out of generosity, not need or want"""
    def __init__(self, af:list[AlternativeFrequencyEntry]=[]) -> None:
        self.af = af
        self.cur_idx = 0
    def get_no_af(self=None): return AF_Codes.NoAF.value << 8 | AF_Codes.Filler.value
    def get_lfmf_follows(self=None): return AF_Codes.LfMf_Follows.value << 8 | AF_Codes.Filler.value
    def get_next(self):
        if len(self.af) > self.cur_idx or len(self.af) > 0:
            out = 0
            if self.cur_idx == 0:
                if self.af[self.cur_idx].lfmf: print("AM can't be the first AF")
                self.cur_idx += 1
                return (AF_Codes.NumAFSBase.value + len(self.af)) << 8 | self.af[0].af_freq
            else:
                try:
                    if not self.af[self.cur_idx].lfmf:
                        out = self.af[self.cur_idx].af_freq << 8
                    else:
                        out = AF_Codes.LfMf_Follows.value << 8
                except IndexError:
                    self.cur_idx = 0
                    return self.get_next()
                if not self.af[self.cur_idx].lfmf:
                    try:
                        if self.af[self.cur_idx + 1]:
                            out |= self.af[self.cur_idx +1].af_freq
                    except IndexError:
                        out |= AF_Codes.Filler.value
                else:
                        out |= self.af[self.cur_idx].af_freq
                self.cur_idx += 1
                if self.cur_idx >= len(self.af): self.cur_idx = 0
                return out
        else:
            self.cur_idx = 0
            return self.get_no_af()
        

class RDSCharset:
    """This function is responsible for encoding the characters for the RDS Charset, as it is diffrent but similiar to utf-8"""
    def translate(self, character:str):
        out = 0
        i = 0
        match ord(character):
            case 0xa1: out = 0x8e #INVERTED EXCLAMATION MARK
            case 0xa3: out = 0xaa #POUND SIGN
            case 0xa7: out = 0xbf #SECTION SIGN
            case 0xa9: out = 0xa2 #COPYRIGHT SIGN
            case 0xaa: out = 0xa0 #FEMININE ORDINAL INDICATOR
            case 0xb0: out = 0xbb #DEGREE SIGN
            case 0xb1: out = 0xb4 #PLUS-MINUS SIGN
            case 0xba: out = 0xb0 #MASCULINE ORDINAL INDICATOR
            case 0xb9: out = 0xb1 #SUPERSCRIPT ONE
            case 0xb2: out = 0xb2 #SUPERSCRIPT TWO
            case 0xb3: out = 0xb3 #SUPERSCRIPT THREE
            case 0xb5: out = 0xb8 #MIKRO SIGN
            case 0xbc: out = 0xbc #VULGAR FRACTION ONE QUARTER
            case 0xbd: out = 0xbd #VULGAR FRACTION ONE HALF
            case 0xbe: out = 0xbe #VULGAR FRACTION THREE QUARTERS
            case 0xbf: out = 0xb9 #INVERTED QUESTION MARK
            case 0x80: out = 0xc1 #LATIN CAPITAL LETTER A WITH GRAVE
            case 0x81: out = 0xc0 #LATIN CAPITAL LETTER A WITH ACUTE
            case 0x82: out = 0xd0 #LATIN CAPITAL LETTER A WITH CIRCUMFLEX
            case 0x83: out = 0xe0 #LATIN CAPITAL LETTER A WITH TILDE
            case 0x84: out = 0xd1 #LATIN CAPITAL LETTER A WITH DIAERESIS
            case 0x85: out = 0xe1 #LATIN CAPITAL LETTER A WITH RING ABOVE
            case 0x86: out = 0xe2 #LATIN CAPITAL LETTER AE
            case 0x87: out = 0x8b #LATIN CAPITAL LETTER C WITH CEDILLA
            case 0x88: out = 0xc3 #LATIN CAPITAL LETTER E WITH GRAVE
            case 0x89: out = 0xc2 #LATIN CAPITAL LETTER E WITH ACUTE
            case 0x8a: out = 0xd2 #LATIN CAPITAL LETTER E WITH CIRCUMFLEX
            case 0x8b: out = 0xd3 #LATIN CAPITAL LETTER E WITH DIAERESIS
            case 0x8c: out = 0xc5 #LATIN CAPITAL LETTER I WITH GRAVE
            case 0x8d: out = 0xc4 #LATIN CAPITAL LETTER I WITH ACUTE
            case 0x8e: out = 0xd4 #LATIN CAPITAL LETTER I WITH CIRCUMFLEX
            case 0x8f: out = 0xd5 #LATIN CAPITAL LETTER I WITH DIAERESIS
            case 0x90: out = 0xce #LATIN CAPITAL LETTER ETH
            case 0x91: out = 0x8a #LATIN CAPITAL LETTER N WITH TILDE
            case 0x92: out = 0xc7 #LATIN CAPITAL LETTER O WITH GRAVE
            case 0x93: out = 0xc6 #LATIN CAPITAL LETTER O WITH ACUTE
            case 0x94: out = 0xd6 #LATIN CAPITAL LETTER O WITH CIRCUMFLEX
            case 0x95: out = 0xe6 #LATIN CAPITAL LETTER O WITH TILDE
            case 0x96: out = 0xd7 #LATIN CAPITAL LETTER O WITH DIAERESIS
            case 0x98: out = 0xe7 #LATIN CAPITAL LETTER O WITH STROKE
            case 0x99: out = 0xc9 #LATIN CAPITAL LETTER U WITH GRAVE
            case 0x9a: out = 0xc8 #LATIN CAPITAL LETTER U WITH ACUTE
            case 0x9b: out = 0xd8 #LATIN CAPITAL LETTER U WITH CIRCUMFLEX
            case 0x9c: out = 0xd9 #LATIN CAPITAL LETTER U WITH DIAERESIS
            case 0x9d: out = 0xe5 #LATIN CAPITAL LETTER Y WITH ACUTE
            case 0x9e: out = 0xe8 #LATIN CAPITAL LETTER THORN
            case 0xa0: out = 0x81 #LATIN SMALL LETTER A WITH GRAVE
            case 0xa1: out = 0x80 #LATIN SMALL LETTER A WITH ACUTE
            case 0xa2: out = 0x90 #LATIN SMALL LETTER A WITH CIRCUMFLEX
            case 0xa3: out = 0xf0 #LATIN SMALL LETTER A WITH TILDE
            case 0xa4: out = 0x91 #LATIN SMALL LETTER A WITH DIAERESIS
            case 0xa5: out = 0xf1 #LATIN SMALL LETTER A WITH RING ABOVE
            case 0xa6: out = 0xf2 #LATIN SMALL LETTER AE
            case 0xa7: out = 0x9b #LATIN SMALL LETTER C WITH CEDILLA
            case 0xa8: out = 0x83 #LATIN SMALL LETTER E WITH GRAVE
            case 0xa9: out = 0x82 #LATIN SMALL LETTER E WITH ACUTE
            case 0xaa: out = 0x92 #LATIN SMALL LETTER E WITH CIRCUMFLEX
            case 0xab: out = 0x93 #LATIN SMALL LETTER E WITH DIAERESIS
            case 0xac: out = 0x85 #LATIN SMALL LETTER I WITH GRAVE
            case 0xad: out = 0x84 #LATIN SMALL LETTER I WITH ACUTE
            case 0xae: out = 0x94 #LATIN SMALL LETTER I WITH CIRCUMFLEX
            case 0xaf: out = 0x95 #LATIN SMALL LETTER I WITH DIAERESIS
            case 0xb0: out = 0xef #LATIN SMALL LETTER ETH
            case 0xb1: out = 0x9a #LATIN SMALL LETTER N WITH TILDE
            case 0xb2: out = 0x87 #LATIN SMALL LETTER O WITH GRAVE
            case 0xb3: out = 0x86 #LATIN SMALL LETTER O WITH ACUTE
            case 0xb4: out = 0x96 #LATIN SMALL LETTER O WITH CIRCUMFLEX
            case 0xb5: out = 0xf6 #LATIN SMALL LETTER O WITH TILDE
            case 0xb6: out = 0x97 #LATIN SMALL LETTER O WITH DIAERESIS
            case 0xb7: out = 0xba #DIVISION SIGN
            case 0xb8: out = 0xf7 #LATIN SMALL LETTER O WITH STROKE
            case 0xb9: out = 0x89 #LATIN SMALL LETTER U WITH GRAVE
            case 0xba: out = 0x88 #LATIN SMALL LETTER U WITH ACUTE
            case 0xbb: out = 0x98 #LATIN SMALL LETTER U WITH CIRCUMFLEX
            case 0xbc: out = 0x99 #LATIN SMALL LETTER U WITH DIAERESIS
            case 0xbd: out = 0xf5 #LATIN SMALL LETTER Y WITH ACUTE
            case 0xbe: out = 0xf8 #LATIN SMALL LETTER THORN
            case 0x87: out = 0xfb #LATIN SMALL LETTER C WITH ACUTE
            case 0x8c: out = 0xcb #LATIN CAPITAL LETTER C WITH CARON
            case 0x8d: out = 0xdb #LATIN SMALL LETTER C WITH CARON
            case 0x91: out = 0xde #LATIN SMALL LETTER D WITH STROKE
            case 0x9b: out = 0xa5 #LATIN SMALL LETTER E WITH CARON
            case 0xb0: out = 0xb5 #LATIN CAPITAL LETTER I WITH DOT ABOVE
            case 0xb1: out = 0x9f #LATIN SMALL LETTER DOTLESS I
            case 0xb2: out = 0x8f #LATIN CAPITAL LIGATURE IJ
            case 0xb3: out = 0x9f #LATIN SMALL LIGATURE IJ
            case 0xbf: out = 0xcf #LATIN CAPITAL LETTER L WITH MIDDLE DOT
            case 0x80: out = 0xdf #LATIN SMALL LETTER L WITH MIDDLE DOT
            case 0x84: out = 0xb6 #LATIN SMALL LETTER N WITH ACUTE
            case 0x88: out = 0xa6 #LATIN SMALL LETTER N WITH CARON
            case 0x8a: out = 0xe9 #LATIN CAPITAL LETTER ENG
            case 0x8b: out = 0xf9 #LATIN SMALL LETTER ENG
            case 0x91: out = 0xa7 #LATIN SMALL LETTER O WITH DOUBLE ACUTE
            case 0x92: out = 0xe3 #LATIN CAPITAL LIGATURE OE
            case 0x93: out = 0xf3 #LATIN SMALL LIGATURE OE
            case 0x94: out = 0xea #LATIN CAPITAL LETTER R WITH ACUTE
            case 0x95: out = 0xfa #LATIN SMALL LETTER R WITH ACUTE
            case 0x98: out = 0xca #LATIN CAPITAL LETTER R WITH CARON
            case 0x99: out = 0xda #LATIN SMALL LETTER R WITH CARON
            case 0x9a: out = 0xec #LATIN CAPITAL LETTER S WITH ACUTE
            case 0x9b: out = 0xfc #LATIN SMALL LETTER S WITH ACUTE
            case 0x9e: out = 0x8c #LATIN CAPITAL LETTER S WITH CEDILLA
            case 0x9f: out = 0x9c #LATIN SMALL LETTER S WITH CEDILLA
            case 0xa0: out = 0xcc #LATIN CAPITAL LETTER S WITH CARON
            case 0xa1: out = 0xdc #LATIN SMALL LETTER S WITH CARON
            case 0xa6: out = 0xee #LATIN CAPITAL LETTER T WITH STROKE
            case 0xa7: out = 0xfe #LATIN SMALL LETTER T WITH STROKE
            case 0xb1: out = 0xb7 #LATIN SMALL LETTER U WITH DOUBLE ACUTE
            case 0xb5: out = 0xf4 #LATIN SMALL LETTER W WITH CIRCUMFLEX
            case 0xb7: out = 0xe4 #LATIN SMALL LETTER Y WITH CIRCUMFLEX
            case 0xb9: out = 0xed #LATIN CAPITAL LETTER Z WITH ACUTE
            case 0xba: out = 0xfd #LATIN SMALL LETTER Z WITH ACUTE
            case 0xbd: out = 0xcd #LATIN CAPITAL LETTER Z WITH CARON
            case 0xbe: out = 0xdd #LATIN SMALL LETTER Z WITH CARON
            case 0xa6: out = 0xa4 #LATIN CAPITAL LETTER G WITH CARON
            case 0xa7: out = 0x9d #LATIN SMALL LETTER G WITH CARON
            case 0xb1: out = 0xa1 #GREEK SMALL LETTER ALPHA
            case 0xb2: out = 0x8d #GREEK SMALL LETTER BETA
            case 0x80: out = 0xa8 #GREEK SMALL LETTER PI
            case 0x24: out = 0xab #DOLLAR SIGN
            case _: out = ord(character)
        return out
class GroupGenerator:
    """This class is responsible for generating RDS groups, such as PS, RT, PTYN, ECC, LIC and CT (experimental, can't test but implementation looks correct)"""
    def basicGroup(pi:int, tp: bool=False, pty: int=0):
        """This function will generate the basics for a group, pass the output of this into the blocks argument of the other groups"""
        return [
            pi & 0xFFFF, #this is not changed by any group
            (int(tp) << 10 | pty << 5) & 0xFFFF, #information and possibly can be some data
            0,0 #arguments for the group
        ]
    def ps(blocks:list,ps_text:str,segment:int,ms:bool=True,ta:bool=False,di:int=1,block2:int=0):
        """This function will generate a PS (0A) group, needs the ps text itself and the current segment to generate, it is meant to be ran in a for loop with, like this:
        for segment in range(4):
            GroupGenerator.ps(basic,'radio95 ',segment)
        max segment is 4"""
        if segment > 4: raise Exception("Segment limit")
        return [
            blocks[0] & 0xFFFF,
            (blocks[1] | int(ta) << 4 | int(ms) << 3 | ((di>>(3-segment)) << 2) | segment) & 0xFFFF,
            int(block2) & 0xFFFF or AlternativeFrequency.get_no_af(),
            (RDSCharset().translate(ps_text[segment*2])<<8 | RDSCharset().translate(ps_text[segment*2+1])) & 0xFFFF,
        ]
    def ps_b(blocks:list,ps_text:str,segment:int,ms:bool=True,ta:bool=False,di:int=1):
        """This function will generate a PS (0B) group, needs the ps text itself and the current segment to generate, it is meant to be ran in a for loop with, like this:
        for segment in range(4):
            GroupGenerator.ps_b(basic,'radio95 ',segment)
        max segment is 4, the diffrence between 0A is that this does not do AF"""
        if segment > 4: raise Exception("Segment limit")
        return [
            blocks[0] & 0xFFFF,
            (0x0800 | blocks[1] | int(ta) << 4 | int(ms) << 3 | ((di>>(3-segment)) << 2) | segment) & 0xFFFF, #0800 is from generate_rds.py of pydemod and from the docs of rds http://www.interactive-radio-system.com/docs/EN50067_RDS_Standard.pdf page 13, 0800 in binary is a 16 bit number with the 5th bit only on, which is the b0 bit
            blocks[0] & 0xFFFF, #http://www.interactive-radio-system.com/docs/EN50067_RDS_Standard.pdf page 15
            (RDSCharset().translate(ps_text[segment*2])<<8 | RDSCharset().translate(ps_text[segment*2+1])) & 0xFFFF,
        ]
    def rt(blocks:list,rt_text:str,segment:int,ab:bool=False):
        """This function will generate a RT (2A) group with a function of A/B, it can be used in a similiar way to PS, max segment is 16"""
        if segment > 16: raise Exception("Segment limit")
        return [
            blocks[0] & 0xFFFF,
            (blocks[1] | 2 << 12 | int(ab) << 4 | segment) & 0xFFFF,
            (RDSCharset().translate(rt_text[segment*4+0])<<8 | RDSCharset().translate(rt_text[segment*4+1])) & 0xFFFF,
            (RDSCharset().translate(rt_text[segment*4+2])<<8 | RDSCharset().translate(rt_text[segment*4+3])) & 0xFFFF
        ]
    def rt_b(blocks:list,rt_text:str,segment:int,ab:bool=False):
        """This function will generate a RT (2B) group with a function of A/B, it can be used in a similiar way to PS, max segment is 16"""
        if segment > 16: raise Exception("Segment limit")
        return [
            blocks[0] & 0xFFFF,
            (0x0800 | blocks[1] | 2 << 12 | int(ab) << 4 | segment) & 0xFFFF,
            blocks[0] & 0xFFFF,
            (RDSCharset().translate(rt_text[segment*2+2])<<8 | RDSCharset().translate(rt_text[segment*2+3])) & 0xFFFF
        ]
    def ptyn(blocks:list,ptyn_text:str,segment:int):
        """This function will generate a PTYN (10A) group, it can be used in a similiar way to RT, max segment is 2"""
        if segment > 2: raise Exception
        return [
            blocks[0] & 0xFFFF,
            (blocks[1] | 10 << 12 | segment) & 0xFFFF,
            (RDSCharset().translate(ptyn_text[segment*4+0])<<8 | RDSCharset().translate(ptyn_text[segment*4+1])) & 0xFFFF,
            (RDSCharset().translate(ptyn_text[segment*4+2])<<8 | RDSCharset().translate(ptyn_text[segment*4+3])) & 0xFFFF
        ]
    def ecc(blocks:list, ecc: int):
        """This function will generate a ECC (1A) group, it can be used to identify the country of the broadcast"""
        return [
            blocks[0] & 0xFFFF,
            (blocks[1] | 1 << 12) & 0xFFFF,
            (blocks[2] | ecc) & 0xFFFF,
            blocks[3] & 0xFFFF
        ]
    def lic(blocks:list, lic: int):
        """This function will generate a LIC (1A) group, it can be used to identify the language of the broadcast"""
        return [
            blocks[0] & 0xFFFF,
            (blocks[1] | 1 << 12) & 0xFFFF,
            (blocks[2] | (lic | 0x3000)) & 0xFFFF,
            blocks[3] & 0xFFFF
        ]
    def ct(blocks: list, hour: int, min: int, year: int, day: int, month: int, hour_local: int=None):
        """This function should generate a CT (4A) group
        FIXME: invalid date/time"""
        def calculate_mjd(month, day, year):
            #http://www.interactive-radio-system.com/docs/EN50067_RDS_Standard.pdf page 82
            l = 1 if month == 1 or month == 2 else 0
            return 14956 + day + int( ( (year-1900) - l) * 365.25) + int( (month + 1 + l * 12) * 30.6001) #this algorighm has a error in the implementation of micro rds, l bozo xd (it does month +2 instead of +1)
        if hour_local: offset = ((hour_local-hour)*(30*60))
        mjd = calculate_mjd(month, day, year)
        blocks= [
            blocks[0] & 0xFFFF,
            blocks[1] | 4 << 12 | (mjd >> 15) & 0xFFF,
            ((mjd << 1) | (hour >> 4)) & 0xFFFF,
            ((hour & 0xF) << 12 | min << 6) & 0xFFFF
        ]
        if hour_local:
            blocks[3] |= (abs(offset) & 0xFFFF)
            if offset < 0: blocks[3] |= 0x20
        return blocks

def pr(blocks):
    """This will print the blocks in a format which can be either outputed to redsea with the -h flag or written to a file for RDS Spy to read"""
    for i in blocks:
        print(hex(i).removeprefix("0x").upper().zfill(4),end=" ",flush=True)
    print(flush=True)
def pr_bit(bits):
    """This will print the blocks in a format which can be either outputed to redsea or to pydemod to modulate"""
    for bit in bits:
        print("1" if int(bit) == 1 else "0",end="",flush=True)
    # print(flush=True)
class GroupInterface:
    """This is a comfort class which will automatically pick the number of segments for a selected type of group"""
    def getPS(text: str, full:bool=False):
        """This function can be used to automatically get the number of segments and the text for PS, so 'radio95' is 7 characters which is not divisible by 2, the function adds a extra space and sets the segments to max as we have 8 characters which is the max
        The function has a 'full' setting which can be used to set the max number of segments instead of the nunber being dependent the the text's lenght"""
        if len(text) > 8: raise Exception
        if not full:
            while len(text) % 2:
                text = text + " "
            segments = 0
            for _ in range(len(text)):
                segments = segments + 0.5
            return text, int(segments)
        else:
            return text.ljust(8), 4
    def getRT(text: str,full:bool=False):
        """Similar to getPS"""
        if len(text) > 64: raise Exception
        if not full:
            while len(text) % 4:
                text = text + " "
            segments = 0
            for _ in range(len(text)):
                segments = segments + 0.25
            return text, int(segments)
        else:
            return text.ljust(64), 16
    def getPTYN(text: str,full:bool=False):
        """Similar to getRT"""
        if len(text) > 8: raise Exception
        if not full:
            while len(text) % 4:
                text = text + " "
            segments = 0
            for _ in range(len(text)):
                segments = segments + 0.25
            return text, int(segments)
        else:
            return text.ljust(8), 2
        
#sequence
class Groups(Enum):
    PS = 0
    RT = 1
    ECC = 2
    LIC = 3
    PTYN = 4
class GroupSequencer:
    def __init__(self, sequence:list[IntEnum]) -> None:
        self.cur_idx = 1
        self.sequence = sequence
    def get_next(self):
        if len(self.sequence) == 0: return
        if self.cur_idx > len(self.sequence)-1: self.cur_idx = 1
        prev = self.sequence[self.cur_idx-1]
        self.cur_idx += 1
        return prev
    def __len__(self):
        return len(self.sequence)

import numpy
class BitGenerator:
    def _generate(wordstream):
        #i stole this code from pydemod https://github.com/ChristopheJacquet/Pydemod
        def to_bin(x):
            res = []
            for _ in range(16):
                res.insert(0, x % 2)
                x >>= 1
            return res
        words = numpy.array([to_bin(ow[1]) for ow in wordstream])
        offsets = numpy.array(list(map(lambda ow: numpy.array({'A': [0, 0, 1, 1, 1, 1, 1, 1, 0, 0], 'B': [0, 1, 1, 0, 0, 1, 1, 0, 0, 0], 'C': [0, 1, 0, 1, 1, 0, 1, 0, 0, 0], "C'": [1, 1, 0, 1, 0, 1, 0, 0, 0, 0], 'D': [0, 1, 1, 0, 1, 1, 0, 1, 0, 0]}[ow[0]]), wordstream)))
        poly = numpy.array([1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1], dtype=int)
        check_size = poly.size - 1
        matp = numpy.empty([0,check_size], dtype=int)
        for i in range(16):
            (q, r) = numpy.polydiv(numpy.identity(16+check_size, dtype=int)[i], poly)
            if check_size - r.size > 0:
                r = numpy.append(numpy.zeros(check_size - r.size, dtype=int), r)
            rr = numpy.mod(numpy.array([r], dtype=int), 2)
            matp = numpy.append(matp, rr, axis=0)
        matg = numpy.append(numpy.identity(16, dtype=int), matp, axis=1)
        bitstream = numpy.dot(words, matg) % 2
        bitstream = bitstream.astype(int)
        offsets = offsets.astype(int)
        bitstream[:,16:] ^= offsets
        return bitstream.flatten()
    def process(blocks: list):
        blockswcheck = [0,0,0,0]
        for i,block in enumerate(blocks):
                if blocks[0] == blocks[2]: # this is a group b
                    blockswcheck[i] = (["A","B","C'","D"][i], block)
                else: blockswcheck[i] = (["A","B","C","D"][i], block)
        return BitGenerator._generate(blockswcheck)


basic = GroupGenerator.basicGroup(0x3073, pty=10)
ps = GroupInterface.getPS("radio95", True)
rt = GroupInterface.getRT(f"radio95 - Program godzinny\r")
seq = GroupSequencer([Groups.PS, Groups.PS, Groups.PS, Groups.PS, Groups.PS, Groups.PS, Groups.RT, Groups.RT, Groups.RT, Groups.RT, Groups.RT, Groups.RT, Groups.ECC])
import time
status_ps = 0
status_rt = 0
for _ in range(int(len(seq)+rt[1])): #for whole rt
    gr = seq.get_next()
    time.sleep(0.08)
    match gr:
        case Groups.PS:
            # pr(GroupGenerator.ps_b(basic, ps[0],status_ps)) # this is for rds spy format
            pr_bit(BitGenerator.process(GroupGenerator.ps_b(basic, ps[0],status_ps)))
            status_ps += 1
            if status_ps >= ps[1]: status_ps = 0
        case Groups.RT:
            pr_bit(BitGenerator.process(GroupGenerator.rt(basic, rt[0],status_rt)))
            # pr(GroupGenerator.rt(basic, rt[0],status_rt))
            status_rt += 1
            if status_rt >= rt[1]: status_rt = 0
        case Groups.ECC:
            # pr(GroupGenerator.ecc(basic, 0xE2))
            pr_bit(BitGenerator.process(GroupGenerator.ecc(basic, 0xE2)))
