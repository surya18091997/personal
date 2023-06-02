arr=[1,4,3]
res=[]
def backtrack(arr,comb):
    print("arr--",arr)
    print("comb--",comb)
    #if len(comb)>:
        #return
    #if sum(comb)==0:
        #res.append(comb.copy())
        #print("res--",res)
        #return
    if len(arr)==0:
        res.append(comb.copy())
        return
    for i,j in enumerate(arr):
        print("i--",i)
        print("j--",j)
        backtrack(arr[:i]+arr[i+1:],comb+[j])

    return res


    
    



print(backtrack(arr,[]))
