arr=[1,4,3,2,5,6,8]
res=[]
def backtrack(arr,comb,summ):
    print("arr--",arr)
    print("comb--",comb)
    if sum(comb)>summ:
        return
    if sum(comb)==summ:
        res.append(comb.copy())
        print("res--",res)
        return
    if len(arr)==0:
        return
    for i,j in enumerate(arr):
        print("i--",i)
        print("j--",j)
        backtrack(arr[:i]+arr[i+1:],comb+[j],summ)

    return res


    
    



print(backtrack(arr,[],8))
