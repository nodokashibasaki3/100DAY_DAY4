import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
import psutil
import time
from threading import Thread
import subprocess
import openai
from dotenv import load_dotenv

class MacBookHelper:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client once
        self.openai_client = openai.OpenAI()
        
        # Cache for task descriptions
        self.description_cache = {}
        
        # Common window patterns and their descriptions
        self.common_patterns = {
            # Email patterns
            "Inbox": "📧 Checking new messages",
            "Draft": "📧 Composing email",
            "Sent": "📧 Reviewing sent items",
            "Calendar": "📅 Managing calendar",
            
            # Browser patterns
            "mail.google.com": "📧 Using Gmail",
            "calendar.google.com": "📅 Using Calendar",
            "docs.google.com": "📝 Using Google Docs",
            "sheets.google.com": "📊 Using Google Sheets",
            "meet.google.com": "🎥 In Google Meet",
            
            # Document patterns
            ".doc": "📝 Editing document",
            ".docx": "📝 Editing document",
            ".xls": "📊 Working on spreadsheet",
            ".xlsx": "📊 Working on spreadsheet",
            ".ppt": "📊 Working on presentation",
            ".pptx": "📊 Working on presentation",
            ".pdf": "📄 Viewing document",
            
            # Development patterns
            ".py": "💻 Writing Python code",
            ".js": "💻 Writing JavaScript code",
            ".html": "💻 Writing HTML",
            ".css": "💻 Writing CSS",
            ".md": "📝 Writing documentation"
        }
        
        self.root = tk.Tk()
        self.root.title("MacBook Helper")
        self.root.attributes('-topmost', True)
        
        # Set window size and position
        self.root.geometry("350x450+0+0")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Configure colors and fonts
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Helvetica', 12))
        self.style.configure('TButton', font=('Helvetica', 12), padding=1)
        self.style.configure('TCheckbutton', background='#f5f5f5', font=('Helvetica', 12))
        self.style.configure('TEntry', font=('Helvetica', 12), padding=1)
        self.style.configure('Treeview', background='#ffffff', fieldbackground='#ffffff', 
                           font=('Helvetica', 12))
        self.style.configure('Treeview.Heading', background='#e0e0e0', font=('Helvetica', 12, 'bold'))
        self.style.configure('Treeview.Item', padding=1)
        self.style.configure('Treeview.Row', padding=1)
        self.style.map('Treeview', background=[('selected', '#0078d7')])
        
        # Load or create tasks file
        self.tasks_file = "tasks.json"
        self.archive_file = "archive.json"
        self.tasks = self.load_tasks()
        self.archived_tasks = self.load_archive()
        
        # Track active applications and their details
        self.active_apps = {}
        self.last_active_app = None
        self.last_active_window = None
        self.app_start_time = {}
        self.window_start_time = {}
        self.MIN_ACTIVE_TIME = 20  # Minimum time in seconds before adding a task
        self.stored_app = None
        self.stored_window = None
        
        # Create GUI elements
        self.create_widgets()
        
        # Start monitoring thread
        self.monitor_thread = Thread(target=self.monitor_applications, daemon=True)
        self.monitor_thread.start()
        
        # Update tasks every second
        self.update_tasks()
        
    def load_tasks(self):
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        return []
    
    def load_archive(self):
        if os.path.exists(self.archive_file):
            with open(self.archive_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_tasks(self):
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f)
    
    def save_archive(self):
        with open(self.archive_file, 'w') as f:
            json.dump(self.archived_tasks, f)
    
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill='both', expand=True)
        
        # Header with gradient background
        header_frame = ttk.Frame(main_frame, style='Header.TFrame')
        header_frame.pack(fill='x', pady=(0, 5))
        
        title_label = ttk.Label(header_frame, text="Tracking Tasks...", 
                              font=('Helvetica', 18, 'bold'), foreground='#333333')
        title_label.pack(side='left', padx=(0, 5))
        
        # Status indicator with icon
        self.status_label = ttk.Label(header_frame, text="✓ Auto-tracking active", 
                                    foreground='#28a745', font=('Helvetica', 12))
        self.status_label.pack(side='right')
        
        # Task input frame with rounded corners
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill='x', pady=(0, 4))
        
        self.task_entry = ttk.Entry(input_frame)
        self.task_entry.pack(side='left', fill='x', expand=True, padx=(0, 3))
        
        add_button = ttk.Button(input_frame, text="Add Task", command=self.add_task, 
                              style='Accent.TButton')
        add_button.pack(side='right')
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=(0, 4))
        
        clear_button = ttk.Button(control_frame, text="Clear Completed", 
                                command=self.clear_completed)
        clear_button.pack(side='left', padx=(0, 3))
        
        archive_button = ttk.Button(control_frame, text="Archive All", 
                                  command=self.archive_all)
        archive_button.pack(side='left')
        
        # Organization dropdown with better styling
        org_frame = ttk.Frame(main_frame)
        org_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(org_frame, text="Organize by:", font=('Helvetica', 12, 'bold')).pack(side='left', padx=(0, 3))
        
        self.org_method = tk.StringVar(value="Type")
        org_menu = ttk.OptionMenu(org_frame, self.org_method, "Type", "Type", "Application", 
                                command=self.on_org_change)
        org_menu.pack(side='left')
        
        # Create Treeview with scrollbar and better styling
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)
        
        # Create Treeview with better styling
        self.tree = ttk.Treeview(tree_frame, columns=('status',), show='tree', 
                               style='Custom.Treeview')
        self.tree.heading('#0', text='Tasks', anchor='w')
        self.tree.heading('status', text='Status', anchor='center')
        self.tree.column('status', width=50, anchor='center')
        
        # Add scrollbar with better styling
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind events to the tree
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)
        self.tree.bind('<Motion>', self.on_tree_motion)
        
        # Stats frame with better styling
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill='x', pady=(4, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Total tasks: 0 | Active: 0 | Completed: 0",
                                   font=('Helvetica', 11), foreground='#666666')
        self.stats_label.pack()
        
        # Configure custom styles
        self.style.configure('Header.TFrame', background='#f0f0f0')
        self.style.configure('Accent.TButton', background='#0078d7', foreground='white')
        self.style.configure('Custom.Treeview', rowheight=24)
        self.style.configure('Custom.Treeview.Item', padding=1)
        
        # Configure tag for completed tasks with better styling
        self.tree.tag_configure('completed', foreground='#999999', 
                              font=('Helvetica', 12, 'overstrike'))
    
    def update_stats(self):
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task['completed'])
        active = total - completed
        self.stats_label.config(text=f"Total tasks: {total} | Active: {active} | Completed: {completed}")
    
    def clear_completed(self):
        # Move completed tasks to archive
        completed_tasks = [task for task in self.tasks if task['completed']]
        self.archived_tasks.extend(completed_tasks)
        self.save_archive()
        
        # Remove completed tasks from active list
        self.tasks = [task for task in self.tasks if not task['completed']]
        self.save_tasks()
        self.refresh_tasks()
    
    def archive_all(self):
        # Move all tasks to archive
        self.archived_tasks.extend(self.tasks)
        self.save_archive()
        
        # Clear all tasks
        self.tasks = []
        self.save_tasks()
        self.refresh_tasks()
    
    def monitor_applications(self):
        while True:
            current_app, current_window = self.get_active_application()
            
            if current_app and current_app != self.last_active_app:
                self.last_active_app = current_app
                self.last_active_window = current_window
                # Store the application if it's not our helper app
                if current_app != "Python" and current_app != "Terminal":
                    self.stored_app = current_app
                    self.stored_window = current_window
            
            elif current_app and current_window != self.last_active_window:
                self.last_active_window = current_window
                # Update stored window if it's not our helper app
                if current_app != "Python" and current_app != "Terminal":
                    self.stored_window = current_window
            
            time.sleep(1)
    
    def is_browser(self, app_name):
        return app_name in ["Google Chrome", "Safari", "Firefox", "Microsoft Edge"]
    
    def get_active_application(self):
        try:
            app_script = 'tell application "System Events" to get name of first process whose frontmost is true'
            app_result = subprocess.run(['osascript', '-e', app_script], capture_output=True, text=True)
            
            if app_result.returncode == 0:
                app_name = app_result.stdout.strip()
                
                window_script = f'''
                tell application "{app_name}"
                    if it is running then
                        try
                            return name of front window
                        on error
                            return "Unknown Window"
                        end try
                    end if
                end tell
                '''
                window_result = subprocess.run(['osascript', '-e', window_script], capture_output=True, text=True)
                window_name = window_result.stdout.strip() if window_result.returncode == 0 else "Unknown Window"
                
                return app_name, window_name
        except Exception as e:
            print(f"Error getting active application: {e}")
        return None, None
    
    def save_app_time(self, app_name):
        if app_name in self.app_start_time:
            start_time = self.app_start_time[app_name]
            duration = datetime.now() - start_time
            minutes = int(duration.total_seconds() / 60)
            
            for task in self.tasks:
                if task['app_name'] == app_name and not task['completed']:
                    task['text'] = f"Using {app_name} ({minutes} minutes)"
                    self.save_tasks()
                    break
    
    def task_exists(self, app_name, window_name):
        # Check if we already have a task for this exact app and window
        for task in self.tasks:
            if (task['app_name'] == app_name and 
                task['window_name'] == window_name and 
                not task['completed']):
                return True
        
        # For non-browser apps, only allow one active task per app
        if not self.is_browser(app_name):
            for task in self.tasks:
                if task['app_name'] == app_name and not task['completed']:
                    # Update the existing task with the new window name
                    task['window_name'] = window_name
                    if app_name == "Microsoft Word":
                        task['text'] = f"Editing: {window_name}"
                    elif app_name == "Microsoft Excel":
                        task['text'] = f"Working on: {window_name}"
                    elif app_name == "Preview":
                        task['text'] = f"Viewing: {window_name}"
                    else:
                        task['text'] = f"Using {app_name}: {window_name}"
                    self.save_tasks()
                    return True
        
        return False
    
    def generate_task_description(self, app_name, window_name):
        try:
            # Check cache first
            cache_key = f"{app_name}:{window_name}"
            if cache_key in self.description_cache:
                return self.description_cache[cache_key]
            
            # Check common patterns
            for pattern, description in self.common_patterns.items():
                if pattern.lower() in window_name.lower():
                    self.description_cache[cache_key] = description
                    return description
            
            # For messaging apps, use a simpler pattern
            messaging_apps = ["Outlook", "Slack", "Microsoft Teams", "Messages", "WhatsApp"]
            if app_name in messaging_apps:
                description = f"💬 Responding to conversation"
                self.description_cache[cache_key] = description
                return description
            
            # Only call OpenAI for unique cases
            prompt = f"""Given that I'm using {app_name} and the window/tab is '{window_name}', 
            generate a concise, descriptive task title that explains what I'm likely doing. 
            Include an appropriate emoji at the start. 
            Do NOT include the application name in the description since it's already shown in the category.
            
            Special rules:
            - If it's an email/messaging app and shows a specific conversation/email/chat,
              use "Responding to" instead of "Working on" since the user is likely replying to that conversation.
            - For other apps, describe the specific action being performed.
            
            The response should be just the task title, nothing else."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are a helpful assistant that generates concise, descriptive task titles. 
                    For messaging/email apps, use "Responding to" when a specific conversation is shown.
                    For other apps, describe the specific action being performed.
                    Never include the application name in the description."""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            task_text = response.choices[0].message.content.strip()
            self.description_cache[cache_key] = task_text
            return task_text
            
        except Exception as e:
            print(f"Error generating task description: {e}")
            return f"Working on: {window_name}"
    
    def add_task(self):
        # Use the stored application and window instead of current
        if self.stored_app and self.stored_window:
            current_app = self.stored_app
            current_window = self.stored_window
            
            # Generate task description using AI
            task_text = self.generate_task_description(current_app, current_window)
            
            # Check if task already exists
            task_exists = False
            for task in self.tasks:
                if task['app_name'] == current_app and task['window_name'] == current_window and not task['completed']:
                    task_exists = True
                    break
            
            if not task_exists:
                task = {
                    'text': task_text,
                    'completed': False,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'auto_tracked': False,
                    'app_name': current_app,
                    'window_name': current_window
                }
                self.tasks.append(task)
                self.save_tasks()
                self.refresh_tasks()
        
        # Clear the entry field
        self.task_entry.delete(0, tk.END)
    
    def on_tree_motion(self, event):
        # Change cursor when hovering over items
        item = self.tree.identify_row(event.y)
        if item and self.tree.parent(item):  # If hovering over a task (not a group)
            self.tree.configure(cursor='hand2')
        else:
            self.tree.configure(cursor='')
    
    def on_tree_click(self, event):
        # Get the item that was clicked
        item = self.tree.identify_row(event.y)
        if item and self.tree.parent(item):  # If a task was clicked (not a group)
            # Get the task text and task object immediately
            task_text = self.tree.item(item)['text']
            task = next((t for t in self.tasks if t['text'] == task_text), None)
            
            if task:
                # Toggle the task's completed status
                task['completed'] = not task['completed']
                if task['completed']:
                    # Move to archive
                    self.archived_tasks.append(task.copy())
                    self.save_archive()
                self.save_tasks()
                self.refresh_tasks()
    
    def on_org_change(self, *args):
        self.refresh_tasks()
    
    def refresh_tasks(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.org_method.get() == "Type":
            # Group tasks by type first
            type_groups = {}
            for task in self.tasks:
                # Extract the type from the task text
                task_type = task['text'].split(':')[0].strip()
                if task_type not in type_groups:
                    type_groups[task_type] = {}
                
                # Then group by application within each type
                app_name = task['app_name']
                if app_name not in type_groups[task_type]:
                    type_groups[task_type][app_name] = []
                type_groups[task_type][app_name].append(task)
            
            # Add type groups to tree
            for task_type, app_groups in type_groups.items():
                type_id = self.tree.insert('', 'end', text=task_type, open=True)
                
                # Add application groups within each type
                for app_name, tasks in app_groups.items():
                    app_id = self.tree.insert(type_id, 'end', text=app_name, open=True)
                    
                    # Sort tasks: completed tasks at the bottom
                    tasks.sort(key=lambda x: x['completed'])
                    
                    for task in tasks:
                        status = "✓" if task['completed'] else "○"
                        item_id = self.tree.insert(app_id, 'end', text=task['text'], values=(status,))
                        
                        # Add visual styling for completed tasks
                        if task['completed']:
                            self.tree.item(item_id, tags=('completed',))
        
        else:  # Application organization
            # Group tasks by application
            app_groups = {}
            for task in self.tasks:
                app_name = task['app_name']
                if app_name not in app_groups:
                    app_groups[app_name] = []
                app_groups[app_name].append(task)
            
            # Add application groups to tree
            for app_name, tasks in app_groups.items():
                app_id = self.tree.insert('', 'end', text=app_name, open=True)
                
                # Sort tasks: completed tasks at the bottom
                tasks.sort(key=lambda x: x['completed'])
                
                for task in tasks:
                    status = "✓" if task['completed'] else "○"
                    item_id = self.tree.insert(app_id, 'end', text=task['text'], values=(status,))
                    
                    # Add visual styling for completed tasks
                    if task['completed']:
                        self.tree.item(item_id, tags=('completed',))
        
        # Configure tag for completed tasks
        self.tree.tag_configure('completed', foreground='gray', font=('Helvetica', 12, 'overstrike'))
        
        self.update_stats()
    
    def delete_task(self, item_id):
        task_text = self.tree.item(item_id)['text']
        self.tasks = [t for t in self.tasks if t['text'] != task_text]
        self.save_tasks()
        self.refresh_tasks()
    
    def update_tasks(self):
        self.refresh_tasks()
        self.root.after(1000, self.update_tasks)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MacBookHelper()
    app.run() 