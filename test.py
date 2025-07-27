list_of_colors = [(255,0,0), (0,0,255)]

no_steps = 100

def LerpColour(c1,c2,t):
    return (c1[0]+(c2[0]-c1[0])*t,c1[1]+(c2[1]-c1[1])*t,c1[2]+(c2[2]-c1[2])*t)

gradient = []
for i in range(len(list_of_colors)-1):
    for j in range(no_steps):
        gradient.append(LerpColour(list_of_colors[i],list_of_colors[i+1],j/no_steps))        
print(gradient)