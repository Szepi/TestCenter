#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import platform
import TestSuite
import configparser
#import TestCase
import subprocess
import os
from SimpleDialog import TextDialog

#@todo: Recent file history
#@todo: Configuration: strict mode, generation mode(?), diffmerge_exec
#@todo: Tooltips
#@todo: Nicer status bar
#@todo: Run selected tests (context menu, global menu)
#@todo: Instead of messagebox, use Labels as popups for showing differences
#@todo: Add progress bar to notify user of progress when running tests
#@todo: Add standard menu items (about, help) 
#@todo: many tabs in Notebook: hide some tabs, scroll them, etc.
#@todo: ordering tabs: alphabetic(?)
#@todo: reordering of tests based on Results

INI_FILE = "testcenter.ini"

def enable_menu_item(menu,entry,enable=True):
    menu.entryconfig(entry,state=(tk.ACTIVE if enable else tk.DISABLED))


class MyStatusBar:
    def __init__(self, master,format_str):
        self.label = ttk.Label(master, text='',  relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X,side=tk.BOTTOM)
        self.format_str = format_str
#        self.label.config(bg='lightgrey')

    def set_data(self, *args):
        self.label.config(text=self.format_str % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()
        
class ResultViewer(ttk.Frame):
    def __init__(self,parent,config,script_name,script_tests):
        ttk.Frame.__init__(self, parent)
        self.config = config
        self.script_tests = script_tests
        self.pack(fill=tk.BOTH, expand=tk.YES)
        treeview = self.treeview = ttk.Treeview(self,columns=('Test','Result'),show="headings")
        treeview.heading('Test', text='Test')
        treeview.heading('Result', text='Result')
        
        vsb = ttk.Scrollbar(orient="vertical", command=treeview.yview)
#                hsb = ttk.Scrollbar(orient="horizontal", command=treeview.xview)
        treeview.configure(yscrollcommand=vsb.set) #, xscrollcommand=hsb.set)
        treeview.grid(column=0, row=0, sticky='nsew', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
#                hsb.grid(column=0, row=1, sticky='ew', in_=self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        for k in sorted(list(script_tests.keys())):
            treeview.insert("", tk.END, iid=k, values = (k, 'N/A'))
            
        if self.is_aqua(): 
            # Mac OS aqua handles right-click in a special fashion 
            treeview.bind('<2>',         self.on_rightclick)
            treeview.bind('<Control-1>', self.on_rightclick)
        else:
            treeview.bind('<3>', self.on_rightclick)
            
#        treeview.bind("<Button-3>", self.on_rightclick)
#        if platform.is_mac():
#            treeview.bind("<Button-1>", self.on_rightclick)
        
        parent.add(self,text=script_name)
            
            
    def is_aqua(self):
        # direct call into Tcl/Tk
        return self.treeview.tk.call('tk', 'windowingsystem')=='aqua'
    
    def on_rightclick(self,event):
        if self.is_aqua() and not event.state & 0x04: # right-click emulation?
#            print("Right click false alarm")
            return
        item = self.treeview.identify('item', event.x, event.y)
#        self.treeview.focus(item)
        self.treeview.selection_set(item)
        test_case = self.script_tests[item]
        
        if not test_case.is_pass():
            self.treeview.after_idle(lambda : self.context_menu(event,item))
        return "break"

    def context_menu(self,event,item):
        test_case = self.script_tests[item]

        menu = tk.Menu(root, tearoff=0)
        menu_item = 0
        # Error --------------------------------------------------------
        menu.add_command(label="Error message", command=
            lambda: messagebox.showinfo("Error message", test_case.err_msg()))
        enable_menu_item(menu,menu_item,test_case.is_err())
        menu_item +=1
        
        menu.add_separator()
        menu_item +=1
        
        # Files that differ  ---------------------------------------------
        def run_diffmerge(file1,file2):
            diffmerge_exec = self.config['DEFAULT'].get('diffmerge_exec',platform.diffmerge_exec()) 
            subprocess.call([diffmerge_exec, "--nosplash", file2,file1])
        menu_diff_files = tk.Menu(menu,tearoff=0)
        if test_case.is_fail():
            match_result = test_case.result_details
            for file_pair in match_result.diff_files():
                menu_diff_files.add_command(label=os.path.basename(file_pair[0])
                    ,command=lambda: run_diffmerge(*file_pair))
        menu.add_cascade(menu=menu_diff_files, label='Diffmerge')
        enable_menu_item(menu,menu_item,test_case.is_fail() and test_case.result_details.diff_files())
        menu_item +=1
        
        # Extra files ----------------------------------------------------
        extra_outfiles = ""
        if test_case.is_fail():
            match_result = test_case.result_details
            extra_outfiles = \
             "\n".join([os.path.basename(f) for f in match_result.extra_outputs()])
             
        menu.add_command(label="Extra outputs"
            , command = lambda: messagebox.showinfo("Extra output files",extra_outfiles)
            )
        enable_menu_item(menu,menu_item,test_case.is_fail() and extra_outfiles!="")
        menu_item +=1

        # Missing files ---------------------------------------------------
        missing_outfiles = ""
        if test_case.is_fail():
            match_result = test_case.result_details
            missing_outfiles = \
             "\n".join([os.path.basename(f) for f in match_result.missing_outputs()])
             
        menu.add_command(label="Missing outputs"
            , command = lambda: messagebox.showinfo("Missing output files",missing_outfiles)
            )
        enable_menu_item(menu,menu_item,test_case.is_fail() and missing_outfiles!="")
        menu_item +=1
        
        # Quick difference -----------------------------------------------
        quick_diff = ""
        if test_case.is_fail():
            match_result = test_case.result_details
            quick_diff = match_result.to_string()
             
#        def long_message_box(title,text):
#            text_frame = tk.Frame(borderwidth=1, relief="sunken")
#            text = tk.Text(wrap="word", background="white", 
#                                borderwidth=0, highlightthickness=0)
#            vsb = tk.Scrollbar(orient="vertical", borderwidth=1,
#                                    command=text.yview)
#            text.configure(yscrollcommand=vsb.set)
#            vsb.pack(in_=text_frame,side="right", fill="y", expand=False)
#            text.pack(in_=text_frame, side="left", fill="both", expand=True)
#            text_frame.pack(side="bottom", fill="both", expand=True)
                    
        menu.add_command(label="Quick difference"
            #, command = lambda: tk.messagebox.showinfo("Quick difference",quick_diff)
            , command = lambda: TextDialog(self, "Quick difference", quick_diff)
            )
        enable_menu_item(menu,menu_item,test_case.is_fail())
        menu_item +=1

        menu.post(event.x_root, event.y_root)

    def on_doubleclick(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        print("you clicked on", item, self.treeview.item(item,"values"))
        
    def update_results(self):
        for k,v in self.script_tests.items():
            self.treeview.set(k,'Result',v.get_result_str())

class Application(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        
        self.test_results = {} # for each script, a ResultViewer
        self.script_source = None
        self.testcase_source = None
        self.script_dir = None # after potentially unzipping the zip file
        self.test_suite = None
        self.verify_script_dir = False # whether the script directory name has to be the same as the assignment name
        self.summary = (0,0,0,0) # Tests, Errs, Soft-test failures, Hard-test failures
        
        self.config = configparser.ConfigParser()
        self.root = master # must be a toplevel window or the root
        self.pack(expand=tk.YES,fill=tk.BOTH) # follow size of parent
        self.createWidgets()
        self.createMenus()
        
        self.update_menustate()

        self.read_config()
        
    def read_config(self):
        config = self.config
        try:
            config.read(INI_FILE)
        except:
            print("Reading config file failed")
            return
        
        dc = config['DEFAULT']
        sst = dc.get('script_source_type',None)
        if sst:
            ss = dc.get('script_source',None)
            if ss:
                self.scripts_changed(sst, ss)
                print("Script source: %s",self.script_source)
        self.testcase_source = dc.get('testcase_source',None)
        print("Testcase source: %s" % self.testcase_source)
        if self.testcase_source:
            self.testcase_changed()
            
        self.verify_script_dir = dc.get('verify_script_dir',False)
     
    
    def write_config(self):
        with open(INI_FILE,'w') as configfile:
            self.config.write(configfile)
    
    # -----------------------------------------------------------------                
    # Building the GUI 
    # -----------------------------------------------------------------                

    def createWidgets(self):
        self.sb3 = MyStatusBar(self,"Script: %s")
        self.sb3.set_data("")
        self.sb2 = MyStatusBar(self,"Testcases: %s")
        self.sb2.set_data("")
        self.sb1 = MyStatusBar(self,"Tests: %s   Errors: %s   Serious fails: %s   All fails: %s")
        self.sb1.set_data(0,0,0,0)
        self.update_statusbar()
        
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=tk.YES, padx=2,pady=3)
        # extend bindings to top level window allowing
        #   CTRL+TAB - cycles thru tabs
        #   SHIFT+CTRL+TAB - previous tab
        #   ALT+K - select tab using mnemonic (K = underlined letter)        
        self.nb.enable_traversal()
        self.empty_notebook()

    def empty_notebook(self):
        self.test_results = {}
        for i in self.nb.tabs():
            self.nb.forget(i)
        rv = self.test_results[''] = ResultViewer(self.nb,self.config,'<script>',dict())
        self.nb.add(rv)

    def add_menu_accelerators(self):
        # @todo enable/disable these as the menu state changes 
        acc = ( ("<Control-z>",lambda x: self.select_script_zip())
              , ("<Control-d>",lambda x: self.select_script_dir())
              , ("<Control-t>",lambda x: self.select_testcase_dir())
              , ("<Control-x>",lambda x: self.root.quit())
              , ("<Control-r>",lambda x: self.runall()) 
        )
        if platform.is_mac():
            acc = ( ("<Command-z>",lambda x: self.select_script_zip())
                  , ("<Command-d>",lambda x: self.select_script_dir())
                  , ("<Command-t>",lambda x: self.select_testcase_dir())
                  , ("<Command-x>",lambda x: self.root.quit())
                  , ("<Command-r>",lambda x: self.runall()) 
            )            
        for a in acc:
            self.root.bind_all(a[0],a[1])        

    def createMenus(self):
        top = tk.Menu(self.root)
        self.root.config(menu=top)
        file = self.menu_file = tk.Menu(top,tearoff=False)
        acc_str = platform.accelerator_string()
        file.add_command(label='Script ZIP file'
            , command=self.select_script_zip, underline=7, accelerator=acc_str+"+Z")
        file.add_command(label='Script directory file'
            , command=self.select_script_dir, underline=7, accelerator=acc_str+"+D")
        file.add_separator()
        file.add_command(label='Testcase directory'
            , command=self.select_testcase_dir, underline=0, accelerator=acc_str+"+T")
        if not platform.is_mac(): # on a mac, quit always exists
            file.add_separator()
            file.add_command(label='Exit'
                , command=self.root.quit, underline=1, accelerator=acc_str+"+X")
        top.add_cascade(label='File', menu=file, underline=0)
        
        run = self.menu_run = tk.Menu(top,tearoff=False)
        run.add_command(label="Run all"
            , command=self.runall, underline=0, accelerator=acc_str+"+R")
        top.add_cascade(label='Run', menu=run, underline=0)
        
        self.add_menu_accelerators()
        
        #@todo take care of special menus (help, apple on Mac, http://tkinter.unpythonic.net/wiki/Widgets/Menu)
        
    # -----------------------------------------------------------------                
    # Update the state of the GUI 
    # -----------------------------------------------------------------
                         
    def update_menustate(self):
        enable_menu_item(self.menu_run,0,self.runall_enabled())

    def update_statusbar(self):
        self.sb3.set_data(self.script_source[1] if self.script_source else None)
        self.sb2.set_data(self.testcase_source)
        self.summary = ((0,0,0,0) if self.test_suite==None else self.test_suite.get_summary())
        self.sb1.set_data(*self.summary)

    def update_notebook(self):
        for v in self.test_results.values():
            v.update_results()

    # -----------------------------------------------------------------                
    # Implementing menu actions 
    # -----------------------------------------------------------------                
        
    def select_script_zip(self):
        zipfile = filedialog.askopenfilename(title='Select a zip-file of the scripts to be tested'
                , filetypes = (("ZIP files", "*.zip"), )
                )
        self.scripts_changed("zip",zipfile)

    def select_script_dir(self):
        fld = filedialog.askdirectory(title='Select the directory of the scripts to be tested')
        self.scripts_changed("dir",fld)
        
    def select_testcase_dir(self):
        fld = filedialog.askdirectory(title='Select the directory containing the testcases')
        if fld:
            self.testcase_source = fld
            
            print("Selected test directory:",fld)
            self.testcase_changed()
                                
    def runall(self):
        if self.runall_enabled():
            try:
                self.prep_submission()
                print("Running tests against the submission files")
                self.test_suite.run_tests(self.script_dir,timeout=5,gen_res=False,visible_space_diff=True,verbose =True)
            except RuntimeError as err:
                tk.messagebox.showerror("Error", str(err))
            self.update_menustate()
            self.update_notebook()            
            self.update_statusbar()


    # -----------------------------------------------------------------                
    # Propagating, managing change of state 
    # -----------------------------------------------------------------                
                
    def runall_enabled(self):
        return self.script_source!=None and self.testcase_source!=None and self.test_suite!=None

    def scripts_changed(self,src_type,src):
        print("scripts_changed: (%s,%s)" % (src_type,src))
        if not src:
            return
        new_source = (src_type,src)
        if new_source!=self.script_source:
            self.script_source = new_source
            self.config['DEFAULT']['script_source_type'] = new_source[0]
            self.config['DEFAULT']['script_source'] = new_source[1]
            self.write_config()
            print("Selected:",new_source[1])
            
            self.script_dir = None
            try:
                self.prep_submission()
            except RuntimeError as err:
                tk.messagebox.showerror("Error", str(err))
                
            self.reset_results()
            self.update_notebook()
            self.files_changed()
    
    def reset_results(self):
        if self.test_suite!=None:
            for test_caselist in self.test_suite.test_cases.values():
                for test_case in test_caselist.values():
                    test_case.reset_result()
        
    def reset_test_suite(self):        
        self.test_suite = None
        self.empty_notebook()
        self.update_statusbar()

    def testcase_changed(self):
        # reset the contents of the notebook
#        num_tabs = self.nb.index("end") # do NOT use numeric indeces with forget: they don't work
#        print(self.nb.tabs()[0])
        print("Creating test suite")
        try:
            self.test_suite = TestSuite.TestSuite(self.testcase_source)
        except RuntimeError as err:
            tk.messagebox.showerror("Error creating the test suite", str(err))
            self.reset_test_suite()
            return
                        
        print("Collecting tests")
        try:
            self.test_suite.collect_tests(create_missing_dirs=False)
        except RuntimeError as err:
            tk.messagebox.showerror("Error collecting the tests", str(err))
            self.reset_test_suite()
            return
            
        print("Collected %s tests" % len(self.test_suite.test_cases))
        self.config['DEFAULT']['testcase_source'] = self.testcase_source
        self.write_config()
        self.init_notebook()
        
        self.files_changed()
        
    def init_notebook(self):
        print("Resetting notebook")
        if self.test_suite==None:
            self.empty_notebook()
            return
        self.test_results = {}
        for i in self.nb.tabs():
            self.nb.forget(i)
        # updating notebook
        for script_name,script_tests in sorted(list(self.test_suite.test_cases.items())):
            print("script_name",script_name)
            rv = self.test_results[script_name] = ResultViewer(self.nb,self.config,script_name,script_tests)
            self.nb.add(rv)

    def files_changed(self):
        self.update_menustate()
        self.update_statusbar()

    def prep_submission(self):
        if self.test_suite!=None and self.script_dir==None:
            print("Verifying submission files")
            self.script_dir = TestSuite.prep_submission(self.script_source[1]
                    ,self.test_suite.assignment_name,self.verify_script_dir)
                

root = tk.Tk()
app = Application(root)
app.master.title('Assignment Test Center')
app.mainloop()     
