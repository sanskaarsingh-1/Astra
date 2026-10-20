from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from typing import Optional

console = Console()

class ProgressReporter:
    def __init__(self, model_name: str, dataset_name: str, total_phases: int = 16):
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.total_phases = total_phases
        self.current_phase = 0
        
        console.print(Panel(f"[bold blue]Astra Training[/bold blue]\n\nModel: {model_name}\nDataset: {dataset_name}", expand=False))
        
    def start_phase(self, phase_name: str):
        self.current_phase += 1
        console.print(f"\n[bold]Phase {self.current_phase}/{self.total_phases}  {phase_name}[/bold] ...")
        
    def finish_phase(self, phase_name: str):
        console.print(f"[bold green]Phase {self.current_phase}/{self.total_phases}  {phase_name}[/bold green]      [✓] 100%")
        
    def log_metrics(self, epoch: int, total_epochs: int, batch: int, total_batches: int, loss: float, lr: float, vram_used: float, vram_total: float):
        console.print(f"Epoch {epoch}/{total_epochs} | Batch {batch}/{total_batches} | Loss: {loss:.4f} | LR: {lr:.2e} | VRAM: {vram_used:.1f}/{vram_total:.1f} GB")
