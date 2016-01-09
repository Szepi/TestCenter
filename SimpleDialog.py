#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk

#@todo: Make the text selectable
#@todo: On a Mac, map Command+W to close

class Dialog(tk.Toplevel):
    def __init__(self, parent, title = ''):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent) # in front of parent, minimized together with it
        self.title(title)
        self.parent = parent
        self.result = None
        # frm fils the whole window --- therefore the dialog becomes themed, too
        frm = self.frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=tk.YES)

        self.buttonbox()

        body = ttk.Frame(frm,relief="sunken")
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5, fill=tk.BOTH, expand=tk.YES)
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = ttk.Frame(self.frm)
        b = ttk.Button(box, text="OK", command=self.ok, default=tk.ACTIVE)
        b.pack(padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack(side=tk.BOTTOM)
        
    #
    # standard button semantics

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()
    #
    # command hooks

    def validate(self):
        return True # override

    def apply(self):
        pass # override
    
class MyDialog(Dialog):

    def body(self, master):
        ttk.Label(master, text="First:").grid(row=0)
        ttk.Label(master, text="Second:").grid(row=1)
        self.e1 = ttk.Entry(master)
        self.e2 = ttk.Entry(master)
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        first = int(self.e1.get())
        second = int(self.e2.get())
        print(first, second) # or something    

class TextDialog(Dialog):
    def __init__(self, parent, title ='', text=''):
        self.text_msg = text
        Dialog.__init__(self, parent, title)
        
    def body(self,master):
        self.text = tk.Text(master,wrap="word", background="white", 
                        borderwidth=0, highlightthickness=0)
        self.vsb = ttk.Scrollbar(master,orient="vertical",
                                command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.insert(tk.END, self.text_msg)
        self.text.config(state=tk.DISABLED)
        self.vsb.pack(in_=master,side=tk.RIGHT,fill="y")
        self.text.pack(in_=master,side=tk.LEFT,fill=tk.BOTH,expand=tk.YES)

if __name__=="__main__":
    text = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
    root = tk.Tk()
    
    style = ttk.Style()
#    print(style.theme_names())
    style.theme_use('classic') # ('aqua', 'clam', 'alt', 'default', 'classic')
    
    root.withdraw()
    dlg = TextDialog(root,"Message",text)
