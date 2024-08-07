import re

# Svi moguci koraci robota
# S - rotiraj cijelu kocku, oko donje/gornje stranice (1 = 90°, 3 = -90°)
# F - okreni cijelu kocku, prednja stranica -> donja stranica
# R - okreni donju stranu, srednja i gornja strana se drže na mjestu

# Koraci se izvrsavaju redoslijedom kako su napisani u rijecniku

moves_dict = {'U':'F2S3R1', 'U2':'F2S3R1S3R1', "U'":'F2S1R3',
              'D':'S3R1',   'D2':'S3R1S3R1',   "D'":'S1R3',
              'F':'F1S3R1', 'F2':'F1S3R1S3R1', "F'":'F1S1R3',
              'B':'F3S3R1', 'B2':'F3S3R1S3R1', "B'":'F3S1R3',
              'L':'S3F3R1', 'L2':'S3F3R1S3R1', "L'":'S1F1R3',
              'R':'S3F1R1', 'R2':'S3F1R1S3R1', "R'":'S1F3R3'}


# Cube orientation at the start, later updated after every cube movement on the robot
h_faces={'L':'L','F':'F','R':'R'}   # dict with faces around the bottom/upper positioned faces
v_faces={'D':'D','F':'F','U':'U'}   # dict with faces around the left/right positioned faces



def starting_cube_orientation():
    """ Defines the starting cube orientation, that has to be recalled in case the robot is operated multiple times in a single session."""
    
    global h_faces,v_faces 
    
    # Cube orientation at the start, later updated after every cube movement on the robot
    h_faces={'L':'L','F':'F','R':'R'}   # dict with faces around the bottom/upper positioned faces
    v_faces={'D':'D','F':'F','U':'U'}   # dict with faces around the left/right positioned faces



def opp_face(face):
    """ This function returns the opposite face of the one in argument."""
    
    if face == 'F': return 'B'
    elif face == 'B': return 'F'
    elif face == 'U': return 'D'
    elif face == 'D': return 'U'
    elif face == 'R': return 'L'
    elif face == 'L': return 'R'
    else:
        return 'Error'


def flip_effect(h_faces,v_faces):
    """ Returns the cube faces orientation after a single Flip action; Only v_faces are affected
        It applies a face shift of these faces, and updates the F face on the h_faces dict."""
    
    v_faces['D']=v_faces['F']
    v_faces['F']=v_faces['U']
    v_faces['U']=opp_face(v_faces['D'])
    h_faces['F']=v_faces['F']


def spinCCW_effect(h_faces,v_faces):
    """ Returns the cube faces orientation after a single CCW spin action; Only h_faces are affected
        It applies a face shiftof these faces, and updates the F face on the v_faces dict."""
    
    h_faces['L']=h_faces['F']
    h_faces['F']=h_faces['R']
    h_faces['R']=opp_face(h_faces['L'])
    v_faces['F']=h_faces['F']


def spinCW_effect(h_faces,v_faces):
    """ Returns the cube faces orientation after a single CW spin action; Only h_faces are affected
        It applies a face shiftof these faces, and updates the F face on the v_faces dict."""
    
    h_faces['R']=h_faces['F']
    h_faces['F']=h_faces['L']
    h_faces['L']=opp_face(h_faces['R'])
    v_faces['F']=h_faces['F']


def cube_orient_update(movement):
    """ This function traks the cube orientation based on the applied movements by the robot.
        Arguments is the applied robot movement.
        The function uses the cube orientation global variables  "h_faces" and "v_faces"."""
        
    global h_faces,v_faces
    
    for i in range(len(movement)):                 # iterates over the string of robot movements
        if movement[i] == 'F':                     # case there is a cube flip on robot movements
            repeats=int(movement[i+1])             # retrieves how many flips
            for j in range(repeats):               # iterates over the amount of flip
                flip_effect(h_faces,v_faces)       # re-order the cube orientation on the robot due to the flip
        
        elif movement[i] == 'S':                   # case there is a cube spin on robot movements
            repeats=int(movement[i+1])             # retrieves how many spin
            if repeats=='3':                       # case the spin is CCW
                spinCCW_effect(h_faces,v_faces)    # re-order the cube orientation on the robot due to the CCW spin
            else:                                  # case the spin is CW
                for j in range(repeats):           # iterates over the amount of spin
                    spinCW_effect(h_faces,v_faces) # re-order the cube orientation on the robot due to the CW spin             


def adapt_move(move):
    """ This function adapts the robot move after verifying on wich side the related face is located.
        The solver considers the cube orientation to don't change, but on the robot it does.
        This function will then swap the face name, instead to move the cube back on the original position
        The function returns a dict with all the robot moves and the total amount."""
    
    global h_faces,v_faces
    
    face_to_turn = move[0]                        # face to be turned according to the solver 
    if len(move) == 1:
        rotations = ""
    else:
        rotations = move[1]                           # rotations (string) to be applied according to the solver 
    
    cube_orientation=h_faces.copy()               # generating a single cube orientation dict with h_faces
    cube_orientation.update(v_faces)              # generating a single cube orientation dict with h_faces and v_faces
    
    solution_in_dict = True                       # boolean for easier code reading... 80% chances the face is in dict...
    
    for side, face in cube_orientation.items():   # iteration over the current cube orientation dict (5 sides)
        if face == face_to_turn:                  # case the face to be turned is in the dictionary value
            return side+rotations                 # the dictionary key is returned, as the effective face location
        else:                                     # case the face to be turned is not in the dictionary value
            solution_in_dict = False              # boolean variable is changed to False
    
    if solution_in_dict == False:                 # case the face to be turned is not in the dictionary value
        return 'B'+rotations                      # the face to be turned must be the 6th one, the B side



def optimize_moves(moves):
    """Removes unnecessary moves that would cancel each other out, to reduce solving moves and time
    These movements are for instance a spin CW followed by a spin CCW, or viceversa."""
    
    optimization = False                 # boolean to track if optimizations are made
    to_optmize=[]                        # empty list to be populated with string index where optimization is possible
    str_length=len(moves)                # length of the robot move string
    idx=0                                # index variable, of optimizable move string locations, to populate the list
    for i in range(0,str_length,2):      # for loop of with steps = 2
        
        if moves[idx:idx+2]=='S1' and moves[idx+2:idx+4] =='S3':  # case S1 is folloved by S3
#                 print(f'S1 followed by S3 at index {idx}')
            optimization = True          # boolean to track optimization is set true
            to_optmize.append(idx)       # list is populated with the index 
            idx+=4                       # string index is increased by four, to skip the 2nd (already included) move  

        elif moves[idx:idx+2]=='S3'and moves[idx+2:idx+4] =='S1': # case S3 is folloved by S1
#                 print(f'S3 followed by S1 at index {idx}')
            optimization = True          # boolean to track optimization is set true
            to_optmize.append(idx)       # list is populated with the index 
            idx+=4                       # string index is increased by four, to skip the 2nd (already included) move  

        idx+=2                           # index variable is increased by two, to analayse next move
        if idx>=str_length+2:            # case the index variable reaches the string end 
            break                        # for loop is interrupted

    if optimization == False:            # case the moves string had no need to be optimized
        return moves                     # original moves are returned

    else:                                # case the moves string has the need to be optimized
        to_remove=[]                     # empty list to be populated with all indididual characters to be removed from the moves
        for i in to_optmize:                        # iteration over the list of moves to be optimized
            to_remove.append((i, i+1, i+2, i+3))    # list is populated with the 4 caracters of the 2 moves
        
        new_moves=''                                # empty string to hold the new robot moves 
        remove = [item for sublist in to_remove for item in sublist] # list of characters is flattened
        for i in range(str_length):                 # iteration over all the characters of original moves
            if i not in remove:                     # case the index is not included in the list of those to be skipped
                new_moves+=moves[i]                 # the character is added to the new string of moves 
        
        return new_moves                            # the new string of robot moves is returned


def count_moves(moves):
    """Counts the total amount of robot movements."""

    robot_tot_moves = 0               # counter for all the robot movements
    for i in range(len(moves)):       # iterates over the string of robot movements
        if moves[i] == 'F':           # case there is a cube flip on robot movements
            flips=int(moves[i+1])     # retrieves how many flips
            robot_tot_moves+=flips    # increases the total amount of robot movements

        elif moves[i] == 'R':         # case there is a layer rotation on robot movements
            robot_tot_moves+=1        # increases by 1 (cannot be more) the total amount of robot movements
        
        elif moves[i] == 'S':         # case there is a cube spin on robot movements
            robot_tot_moves+=1        # increases by 1 (cannot be more) the total amount of robot movements
    
    return robot_tot_moves            # total amount of robot moves is returned


def robot_moves(solution):
    """ This function splits the cube manouvre from Kociemba solver string, and generates a dict with all the robot movements."""
    
    global h_faces,v_faces
    
    solution = solution.replace(" ", ",")            # eventual empty spaces are removed from the string
    starting_cube_orientation()                   # Cube orientation at the start, later updated after every cube movement on the robot
    robot={}                                      # empty dict to store all the robot moves
    moves = ''                                      # empty string to store all the robot moves
    robot_tot_moves = 0                           # counter for all the robot movements
    
    #blocks = int(round(len(solution)/2,0))    # total amount of blocks of movements (i.e. U2R1L3 are 3 blocks: U2, R1 and L1)

    move_list = re.findall(r'[RLUDFB]\'?[0-2]?', solution)

    # cube orientation and robot movement sequence selection
    for x, move in enumerate(move_list, start=0):               
        adapted_move = adapt_move(move)                   # the move from solver is adapted considering the real cube orientation
        robot_seq = moves_dict[adapted_move]              # robot movement sequence is retrieved
        robot[x] = robot_seq                          # robot movements dict is updated
        moves += robot_seq                                # robot movements string is updated
        cube_orient_update(robot_seq)                   # cube orientation updated after the robot move from this block
                        
    moves = optimize_moves(moves)               # removes unnecessary moves (that would cancel each other out)
    robot_tot_moves = count_moves(moves)      # counter for the total amount of robot movements
    
    return moves #robot, moves, robot_tot_moves  # returns a dict with all the robot moves, string with all the moves and total robot movements

