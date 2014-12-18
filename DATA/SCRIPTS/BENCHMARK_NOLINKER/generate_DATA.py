#!/usr/bin/env python

from __future__ import print_function
import IMP
import IMP.atom
import IMP.core
import IMP.algebra
import IMP.container
import IMP.isd
import math
import random
import optparse                                                                  
import difflib                                                                   
                                                                                 
parser = optparse.OptionParser(description='Generate FRET data')
parser.add_option('--pdb',       dest="pdbs", action="append", default=[], help="Pdb files")
parser.add_option('--name',      dest="names", action="append", default=[], help="Name of the proteins")
parser.add_option('--datafile',   dest="datafile",     help="Name of output file", default="data.out") 
parser.add_option('--ntrials',    dest="ntrials",      help="Number of trials")        
parser.add_option('--pbl',        dest="pbl",          help="Photobleaching probability", default="1.0")
parser.add_option('--Ida',        dest="Ida",          help="Ida value",    default="6.0")
parser.add_option('--Kda',        dest="Kda",          help="kda value")
parser.add_option('--Sigma0',     dest="Sigma0",       help="Sigma0 value")
parser.add_option('--R0',         dest="R0",           help="R0 value", default="49.0")
parser.add_option('--sensitivity',dest="sens",         help="Sensitivity")            

result,args=parser.parse_args()
if len(args) != 0:
    parser.error("wrong number of arguments")

# check stuff
if(len(result.pdbs)!=len(result.names)):
  print("one name per pdb file is needed")
  exit()

# parameters
NTRIALS_=int(result.ntrials)
PBL_=float(result.pbl)
IDA_=float(result.Ida)
KDA_=float(result.Kda)
SIGMA0_=float(result.Sigma0)
R0_=float(result.R0)
SENSITIVITY_=float(result.sens)                                               

# create model
m=IMP.Model()                                                                    

# prepare restraint set
rst_dict={}

def load_pdb(name,filename):                                                     
    prot=IMP.atom.read_pdb(filename,m,IMP.atom.CAlphaPDBSelector())              
    prot.set_name(name)                                                          
    return prot                                                                  

def get_atoms(prot):
    atoms=[]                                                              
    for atom in IMP.atom.get_by_type(prot, IMP.atom.ATOM_TYPE):                  
        residue=IMP.atom.Residue(IMP.atom.Atom(atom).get_parent())               
        restype=residue.get_residue_type()                                       
        vol=IMP.atom.get_volume_from_residue_type(restype)                       
        radius=IMP.algebra.get_ball_radius_from_volume_3d(vol)                   
        IMP.core.XYZR(atom).set_radius(radius)                                   
        atoms.append(atom)                                                
    return atoms

def create_rigid_body(atoms):
    prb=IMP.Particle(m)                                                          
    rb=IMP.core.RigidBody.setup_particle(prb,atoms)                              
    return rb

def get_grid(gmin,gmax,ngrid,boundaries):
    grid=[]
    dx = ( gmax - gmin ) / float(ngrid)
    for i in range(0,ngrid+1):
        if(not boundaries and i==0): continue
        if(not boundaries and i==ngrid): continue
        grid.append( gmin + float(i) * dx )
    return grid

def get_log_grid(gmin,gmax,ngrid):
   grid=[]
   for i in range(0,ngrid+1):
       grid.append( gmin*math.exp(float(i)/ngrid*math.log(gmax/gmin)) )
   return grid

fmod_grid=get_grid(0.01, 10., 10000, True)

def get_probability(fmod, fexp, sigma0):
    # auxiliary stuff                                                            
    log_eps = math.log(fexp/fmod);                                               
    # return probability                                                         
    prob = math.sqrt(2.)*sigma0/fexp/math.pi/(log_eps*log_eps + 2.*sigma0*sigma0)
    return prob
 
def get_random_data_point(expected_value,ntrials,sensitivity):                   

    a=[]                                                                         
    for i in range(0,ntrials):                                                   
        a.append([random.random(),True])                                         
    norm=0.                                                                       
    cumul=[]                                                                     
    cumul.append(0.)                                                              
    for j in range(1,len(fmod_grid)):                                            
        fj=fmod_grid[j]                                                          
        fjm1=fmod_grid[j-1]                                                      
        df = fj - fjm1                                                           
                                                                                 
        pj   = get_probability(fj,   expected_value, SIGMA0_)
        pjm1 = get_probability(fjm1, expected_value, SIGMA0_)

        norm+= (pj+pjm1)/2.0*df;                                                 
        cumul.append(norm)                                                       
    
    random_points=[]                                                             
    for i in range(len(cumul)):                                                  
        for aa in a:                                                             
            if (aa[0]<=cumul[i]/norm and aa[1]):                                 
               random_points.append(int(fmod_grid[i]/sensitivity)*sensitivity)   
               aa[1]=False                                                       
    rmean=0.; rmean2=0.                                                          
    for r in random_points:                                                      
        rmean+=r                                                                 
        rmean2+=r*r                                                              
    rmean/=float(ntrials)                                                        
    rmean2/=float(ntrials)                                                       
    stddev=math.sqrt(max(rmean2-rmean*rmean,0.))                                 
    return rmean,stddev

# read pdb files, coarse grained with CA
molecules={}
for i in range(0,len(result.pdbs)):
    prot=load_pdb(result.names[i],result.pdbs[i])
    molecules[result.names[i]]=prot

# list of particles for N and C termini 
ps={};
for key in molecules:
    # get list of atoms                                                              
    prot_atoms=get_atoms(molecules[key])
    # add to particle dictionary 
    ps[key+"-N"]=[prot_atoms[0].get_particle()]
    ps[key+"-C"]=[prot_atoms[-1].get_particle()]

# create particles
# kda particle                                                                   
kda=IMP.isd.Scale.setup_particle(IMP.Particle(m),KDA_)
kda.set_lower(KDA_)                                                          
kda.set_upper(KDA_)                                                          
kda.set_is_optimized(kda.get_nuisance_key(),False)                                
# Ida particle                                                                   
Ida=IMP.isd.Scale.setup_particle(IMP.Particle(m),IDA_)                          
Ida.set_lower(IDA_)
Ida.set_upper(IDA_)
Ida.set_is_optimized(Ida.get_nuisance_key(),False)                                
# Sigma0 particle
Sigma0=IMP.isd.Scale.setup_particle(IMP.Particle(m),SIGMA0_)                          
Sigma0.set_lower(SIGMA0_)                                                               
Sigma0.set_upper(SIGMA0_)                                                             
Sigma0.set_is_optimized(Ida.get_nuisance_key(),False)
# Pbleaching particle
Pbl=IMP.isd.Scale.setup_particle(IMP.Particle(m),PBL_)
Pbl.set_lower(PBL_)                                                               
Pbl.set_upper(PBL_)                                                             
Pbl.set_is_optimized(Ida.get_nuisance_key(),False)
# R0 particle
R0=IMP.isd.Scale.setup_particle(IMP.Particle(m),R0_)                          
R0.set_lower(R0_)                                                               
R0.set_upper(R0_)                                                             
R0.set_is_optimized(Ida.get_nuisance_key(),False)

# output dictionary
output={}                                                                        
output["PDBs"]=result.pdbs                                                    
output["Kda"]=KDA_
output["Ida"]=IDA_
output["Pbl"]=PBL_
output["Sigma0"]=SIGMA0_
output["R0"]=R0_
output["Sensitivity"]=SENSITIVITY_
output["Ntrials"]=NTRIALS_

# create restraints between all molecules, N and C termini
for i in range(0,len(result.names)-1):
 for ter_i in ("N","C"):
   ni=result.names[i]+"-"+ter_i
   for j in range(i+1,len(result.names)):                                           
    for ter_j in ("N","C"):
     nj=result.names[j]+"-"+ter_j
     rst=IMP.isd.FretRestraint(ps[ni],ps[nj],kda,Ida,R0,Sigma0,Pbl,1.0)
     rst.set_name(ni+"_"+nj)
     mf=rst.get_model_fretr()
     (rdp,rdpstddev)=get_random_data_point(mf,NTRIALS_,SENSITIVITY_)               
     output["Data_Point_Average|"+rst.get_name()]=((ni,nj),rdp)
     output["Data_Point_StdDev|"+rst.get_name()]=rdpstddev
     output["Model_Frequency|"+rst.get_name()]=mf

# open log file                                                                  
log=open(result.datafile,'w')
# write dictionary
log.write("%s \n" % output)
