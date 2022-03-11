import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LogNorm
import matplotlib.transforms as transforms
import scipy.special as sciSpec
import subprocess
import tfs

import Backend.Constants as cst





##############################################################
def get_tracking_string(particleData):
    '''
    Creates tracking string from particle initial coordinates.
    ----------------------------------------------------------
    Input:
        particleData: pd.Series/dict containing canonical or action-angle coordinates
    Output:
        trackingCmd: formated string "start,x=0,px=0,y=0,py=0,t=0,pt=0,fx=0,phix=0,fy=0,phiy=0,ft=0,phit=0;"
        (Default value is 0 for all coordinates)
    '''

    coordinates = ['x','px','y' ,'py' ,'t' ,'pt', 'fx','phix','fy','phiy','ft','phit']
    trackingCmd = ['start']
    trackingCmd += [f'{coord}={particleData.get(coord,0)}' for coord in coordinates]
    trackingCmd = ','.join(trackingCmd)
    return trackingCmd
##############################################################


##############################################################
def MADTrackParticles(madInstance,coordinates,NTurns = 1,saveFile = None,onepass='onepass'):

    trackingCmds = coordinates.apply(get_tracking_string,axis=1)
    trackingCmds = ';\n'.join(trackingCmds)
    
    saveCmd = ''
    if saveFile is not None:
        saveCmd = f'WRITE, TABLE=trackone, FILE={saveFile}'
    
    madCall = ( f"track,dump,{onepass}, onetable = true,file=trackone.trk;\n"
                f"\n"
                f"!{40*'-'}\n"
                f"{trackingCmds};\n"
                f"!{40*'-'}\n"
                f"\n"
                f"run,turns={NTurns};\n"
                f"endtrack;\n"
                f"{saveCmd};")

    madInstance.input(madCall)
##############################################################


##############################################################
##############################################################
def seqedit(sequence,editing, makeThin = False):
    
    # Sorting to install in order:
    editing.sort_values('at',inplace=True)

    output = ''
    if makeThin:
        output = f'''
        use, sequence = {sequence};
        makethin,sequence = {sequence};'''
    
    # install,element = multipole_wire_1of2,class=_multipole_wire_1of2 ,at = 0.5
    elementsEntry = '\n'.join([f'{row["mode"]},element = {row["name"]},class={row["definition"].split(":")[0]},at = {row["at"]};' for _,row in editing.iterrows()])
    definitionEntry = '\n'.join(editing['definition'])
                               
    
    output += f'''
    
        {definitionEntry}
    
        use, sequence = {sequence};
        SEQEDIT, SEQUENCE={sequence};
            FLATTEN;
            {elementsEntry}
            FLATTEN;
        ENDEDIT;

        use, sequence = {sequence};
    '''
    
    if makeThin:
        output += f'''
        use, sequence = {sequence};
        makethin,sequence = {sequence};'''
    
                               
    return output
##############################################################
##############################################################
                               
                               
                            
##############################################################
madSetup = '''
!-------------------
! Defining sequence
!-------------------

{name}:sequence, refer = center, L={L_seq};
!------------------------
!------------------------
endsequence;


!-------------------
! Defining Beam 
!-------------------
beam,   particle = proton,
        charge   = 1,
        npart    = 1,
        energy   = {Energy}/1e9;

!-------------------
! Twiss and MakeThin
!-------------------
use, sequence = {name}; 
makethin,sequence = {name};
'''
##############################################################
                               
                               
##############################################################

madMatch = '''
    use, period = {name};
    match;

    vary, name=K_Qf,step=.001,UPPER=5,LOWER=-5;
    vary, name=K_Qd,step=.001,UPPER=5,LOWER=-5;
    
    constraint,range=#end,mux={mux},muy={muy};

    lmdif,calls=100;
    endmatch;


    title, 'Twiss';
    twiss;
'''
##############################################################
                               
                               

##############################################################
def plotElements(twissDF,ax=None):
    if ax is None:
        ax = plt.gca()
        
    ax.plot(twissDF['s'],0*twissDF['s'],'k')

    colors = {'quadrupole':'C3','multipole':'C2','sbend':'C0'}
    alpha = 0.5
    linewidth = 3
    
    # Adding Quadrupoles:
    keyword = 'quadrupole'
    for index,element in twissDF[twissDF['keyword']==keyword].iterrows():
        ax.add_patch(patches.Rectangle(
            (element.s-element.l, 0),   # (x,y)
            element.l,          # width
            element.k1l,          # height
            color=colors[keyword], alpha=alpha,lw=linewidth ))
        
    # Adding Multipoles:
    keyword = 'multipole'
    for index,element in twissDF[twissDF['keyword']==keyword].iterrows():
        ax.add_patch(patches.Rectangle(
            (element.s-element.l, 0),   # (x,y)
            element.l,          # width
            element.k1l,          # height
            color=colors[keyword], alpha=alpha,lw=linewidth ))
        
    # Adding Multipoles:
    keyword = 'sbend'
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    for index,element in twissDF[twissDF['keyword']==keyword].iterrows():
        if element.angle !=0:
            height = 1/8
            ax.add_patch(patches.Rectangle(
                (element.s-element.l, 0.5-height/2),   # (x,y)
                element.l,          # width
                height,          # height
                color=colors[keyword], alpha=alpha,lw=linewidth,transform=trans ))


##############################################################
