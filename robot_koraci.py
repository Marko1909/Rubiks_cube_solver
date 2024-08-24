import re

# Svi mogući koraci robota
# S - rotiraj cijelu kocku, oko donje/gornje stranice (1 = 90°, 3 = -90°)
# F - okreni cijelu kocku, prednja stranica -> donja stranica
# R - okreni donju stranu, srednja i gornja strana se drže na mjestu

# Koraci se izvršavaju redoslijedom kako su napisani u rječniku
moves_dict = {'U':'F2S3R1', 'U2':'F2S3R1S3R1', "U'":'F2S1R3',
              'D':'S3R1',   'D2':'S3R1S3R1',   "D'":'S1R3',
              'F':'F1S3R1', 'F2':'F1S3R1S3R1', "F'":'F1S1R3',
              'B':'F3S3R1', 'B2':'F3S3R1S3R1', "B'":'F3S1R3',
              'L':'S3F3R1', 'L2':'S3F3R1S3R1', "L'":'S1F1R3',
              'R':'S3F1R1', 'R2':'S3F1R1S3R1', "R'":'S1F3R3'}


# Početna orijentacija kocke
h_faces={'L':'L','F':'F','R':'R'}
v_faces={'D':'D','F':'F','U':'U'}


# Radi promjene orijentacije, potrebno na početku nove izrade postaviti početne orijentacije 
def starting_cube_orientation():
    global h_faces,v_faces 
    
    h_faces={'L':'L','F':'F','R':'R'}
    v_faces={'D':'D','F':'F','U':'U'}

# Vračanje suprotne stranice od ulazne, radi kretanja kocke i promjene orijentacije
def opp_face(face):
    if face == 'F': return 'B'
    elif face == 'B': return 'F'
    elif face == 'U': return 'D'
    elif face == 'D': return 'U'
    elif face == 'R': return 'L'
    elif face == 'L': return 'R'
    else:
        return 'Error'

# Promjena orijentacija stranica nakon flipa
def flip_effect(h_faces,v_faces):
    v_faces['D']=v_faces['F']
    v_faces['F']=v_faces['U']
    v_faces['U']=opp_face(v_faces['D'])
    h_faces['F']=v_faces['F']


# Promjena orijentacija stranica nakon okretanja kocke CCW
def spinCCW_effect(h_faces,v_faces):
    h_faces['L']=h_faces['F']
    h_faces['F']=h_faces['R']
    h_faces['R']=opp_face(h_faces['L'])
    v_faces['F']=h_faces['F']

# Promjena orijentacija stranica nakon okretanja kocke CW
def spinCW_effect(h_faces,v_faces):    
    h_faces['R']=h_faces['F']
    h_faces['F']=h_faces['L']
    h_faces['L']=opp_face(h_faces['R'])
    v_faces['F']=h_faces['F']


# Funkcija za pračenje i ažuriranje orijentacija stranica kocke
def cube_orient_update(movement):  
    global h_faces,v_faces
    
    for i in range(len(movement)):
        if movement[i] == 'F':                     # Ako je flip
            repeats=int(movement[i+1])             # Broj ponavljanja
            for j in range(repeats):
                flip_effect(h_faces,v_faces)       # Ažuriranje orijentacija
        
        elif movement[i] == 'S':                   # Ako je kocka okrenuta
            repeats=int(movement[i+1])             # Broj ponavljanja 
            if repeats=='3':                       # Ako je okretanje CCW
                spinCCW_effect(h_faces,v_faces)    # Ažuriranje orijentacija
            else:                                  # Ako je okretanje CW
                for j in range(repeats):           # Broj ponavljanja
                    spinCW_effect(h_faces,v_faces) # Ažuriranje orijentacija             


# Pronalaženje pozicije stranice za trenutni korak
def adapt_move(move):
    global h_faces,v_faces
    
    face_to_turn = move[0]                        # Stranica za trenutni korak 
    if len(move) == 1:
        rotations = ""
    else:
        rotations = move[1]                       # Broj ponavljanja  
    
    cube_orientation=h_faces.copy()
    cube_orientation.update(v_faces)
        
    solution_in_dict = True
    
    for side, face in cube_orientation.items():
        if face == face_to_turn:                  # Ako je stranica u postavljenim orijentacijama
            return side+rotations 
        else:                                     # Ako stranica nije u postavljenim orijentacijama
            solution_in_dict = False 
    
    if solution_in_dict == False:                 
        return 'B'+rotations


# Uklanjanje potencijalnih ponavljajučih ili međusobno poništavajućih koraka
def optimize_moves(moves): 
    optimization = False
    to_optmize=[]
    str_length=len(moves)
    idx=0
    for i in range(0,str_length,2):
        
        if moves[idx:idx+2]=='S1' and moves[idx+2:idx+4] =='S3':  # Ako se S3 pojavi iza S1 
            optimization = True
            to_optmize.append(idx)
            idx+=4  

        elif moves[idx:idx+2]=='S3'and moves[idx+2:idx+4] =='S1': # Ako se S1 pojavi iza S3
            optimization = True
            to_optmize.append(idx)
            idx+=4

        idx+=2                           # Index se povečava za 2 radi analize sljedećeg koraka
        if idx>=str_length+2:
            break

    if optimization == False:            # Ako nema optimizacije
        return moves

    else:                                # Ako je potrebna optimizacija
        to_remove=[]
        for i in to_optmize:                        # Koraci za optimizaciju
            to_remove.append((i, i+1, i+2, i+3))
        
        new_moves=''
        remove = [item for sublist in to_remove for item in sublist]
        for i in range(str_length):                 
            if i not in remove:
                new_moves+=moves[i]
        
        return new_moves


# Funkcija za pretvaranje Kociemba korake u korake za robota
def robot_moves(solution):
    global h_faces,v_faces
    
    solution = solution.replace(" ", ",")
    starting_cube_orientation()
    robot={}
    moves = ''

    move_list = re.findall(r'[RLUDFB]\'?[0-2]?', solution) # Stvaranje liste iz stringa

    # Orijentacija kocke i izbor koraka za robota 
    for x, move in enumerate(move_list, start=0):               
        adapted_move = adapt_move(move)           # Prilagodba koraka po trenutnoj orijentaciji
        robot_seq = moves_dict[adapted_move]      # Izbor koraka za robota iz rječnika
        robot[x] = robot_seq
        moves += robot_seq
        cube_orient_update(robot_seq)
                        
    moves = optimize_moves(moves)

    return moves 

