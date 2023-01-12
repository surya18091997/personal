def callback(callback_func,*cargs,**ckwargs):
    def dec1(func):
        def modded_deco():
            if not callable(callback_func):
                return func()
            initial_func_return_val =  func()
            if initial_func_return_val:
                return callback_func(initial_func_return_val,*cargs,**ckwargs)
            return callback_func(*cargs,**ckwargs)
        return modded_deco
    return dec1
