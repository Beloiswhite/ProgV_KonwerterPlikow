"""Tkinter/ttk window. Contains no conversion logic: it only calls the registry and the service."""

import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from konwerter.errors import ConversionError, OutputExistsError
from konwerter.registry import available_targets, supported_pairs
from konwerter.service import LOG_FILE, ConversionRequest, execute

POLL_INTERVAL_MS = 100


class ConverterApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=12)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.busy = False

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose an input file.")

        self._build_widgets()
        self.source_var.trace_add("write", lambda *_: self._refresh_targets())
        for var in (self.output_var, self.target_var):
            var.trace_add("write", lambda *_: self._update_controls())
        self._update_controls()

    def _build_widgets(self) -> None:
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Input file:").grid(row=0, column=0, sticky="w", pady=4)
        self.source_entry = ttk.Entry(self, textvariable=self.source_var, width=60)
        self.source_entry.grid(row=0, column=1, sticky="ew", padx=6)
        self.source_button = ttk.Button(self, text="Browse…", command=self._choose_source)
        self.source_button.grid(row=0, column=2)

        ttk.Label(self, text="Output folder:").grid(row=1, column=0, sticky="w", pady=4)
        self.output_entry = ttk.Entry(self, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=6)
        self.output_button = ttk.Button(self, text="Browse…", command=self._choose_output)
        self.output_button.grid(row=1, column=2)

        ttk.Label(self, text="Target format:").grid(row=2, column=0, sticky="w", pady=4)
        self.target_combo = ttk.Combobox(self, textvariable=self.target_var, state="readonly", width=10)
        self.target_combo.grid(row=2, column=1, sticky="w", padx=6)

        buttons = ttk.Frame(self)
        buttons.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 4))
        self.convert_button = ttk.Button(buttons, text="Convert", command=self._convert)
        self.convert_button.pack(side="right")
        ttk.Button(buttons, text="Supported formats", command=self._show_supported).pack(side="left")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Label(self, textvariable=self.status_var, wraplength=520).grid(
            row=5, column=0, columnspan=3, sticky="w"
        )

    def _choose_source(self) -> None:
        patterns = " ".join(f"*{suffix}" for suffix in sorted({src for src, _ in supported_pairs()}))
        path = filedialog.askopenfilename(
            title="Choose an input file",
            filetypes=[("Supported files", patterns), ("All files", "*.*")],
        )
        if path:
            self.source_var.set(path)
            if not self.output_var.get():
                self.output_var.set(str(Path(path).parent))

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Choose an output folder")
        if path:
            self.output_var.set(path)

    def _refresh_targets(self) -> None:
        source = self.source_var.get().strip()
        targets = available_targets(Path(source)) if source else []
        self.target_combo["values"] = targets
        self.target_var.set(targets[0] if targets else "")
        if source and not targets:
            self.status_var.set(f"Files of type '{Path(source).suffix or 'none'}' cannot be converted. "
                                "Click 'Supported formats' to see what is supported.")
        elif targets:
            self.status_var.set("Choose a target format and click Convert.")
        self._update_controls()

    def _update_controls(self) -> None:
        ready = all(var.get().strip() for var in (self.source_var, self.output_var, self.target_var))
        self.convert_button.state(["!disabled"] if ready and not self.busy else ["disabled"])
        inputs_state = ["disabled"] if self.busy else ["!disabled"]
        for widget in (self.source_entry, self.source_button, self.output_entry, self.output_button,
                       self.target_combo):
            widget.state(inputs_state)

    def _convert(self) -> None:
        request = ConversionRequest(
            Path(self.source_var.get().strip()), self.target_var.get(), Path(self.output_var.get().strip())
        )
        overwrite = False
        try:
            request.validate()
        except OutputExistsError:
            if not messagebox.askyesno("File exists", f"{request.output_path} already exists.\nOverwrite it?"):
                self.status_var.set("Conversion cancelled.")
                return
            overwrite = True
        except ConversionError as error:
            self._show_error(str(error))
            return

        self._set_busy(True)
        self.status_var.set(f"Converting {request.source.name} to {request.target_suffix}…")
        future = self.executor.submit(execute, request, overwrite)
        self.after(POLL_INTERVAL_MS, self._check_result, future)

    def _check_result(self, future: Future) -> None:
        if not future.done():
            self.after(POLL_INTERVAL_MS, self._check_result, future)
            return
        self._set_busy(False)
        try:
            result = future.result()
        except ConversionError as error:
            self._show_error(str(error))
        except Exception:  # already logged with a traceback by execute()
            self._show_error(f"Unexpected error. Details were written to {LOG_FILE}.")
        else:
            self.status_var.set(f"Saved: {result}")
            messagebox.showinfo("Done", f"File saved:\n{result}")

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
        self._update_controls()

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        messagebox.showerror("Conversion failed", message)

    def _show_supported(self) -> None:
        lines = [f"{src}  →  {dst}" for src, dst in supported_pairs()]
        messagebox.showinfo("Supported formats", "\n".join(lines))


def run() -> None:
    root = tk.Tk()
    root.title("File Converter")
    root.minsize(560, 0)
    ConverterApp(root).pack(fill="both", expand=True)
    root.mainloop()
