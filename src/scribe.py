"""
ProtoNomia Scribe
A utility class for rich console output formatting using cyberpunk colors.
"""
from typing import Dict, Any

from rich.console import Console
from rich.text import Text

# Initialize rich console
console = Console()

# Cyberpunk color scheme
class Colors:
    """Cyberpunk color scheme for rich text output"""
    AGENT = "bright_magenta"  # Neon Pink for agent names
    CREDITS = "bright_green"  # Neon Green for credits
    ACTION = "bright_yellow"  # Neon Orange for actions
    GOOD = "bright_blue"  # Neon Blue for goods
    NEED = "bright_cyan"  # Neon Purple for needs
    HIGHLIGHT = "bright_white"  # White for highlights
    DAY = "bright_red"  # Red for day markers
    NARRATIVE = "white"  # Default for narrative text


class Scribe:
    """
    The Scribe is responsible for all rich text output in the simulation.
    It formats and colorizes output for better readability and aesthetic.
    """

    @staticmethod
    def format_agent(agent_name: str) -> Text:
        """Format an agent name with appropriate styling"""
        return Text(agent_name, style=Colors.AGENT)

    @staticmethod
    def format_credits(amount: float) -> Text:
        """Format credit amount with appropriate styling"""
        return Text(f"{amount:.0f}", style=Colors.CREDITS)

    @staticmethod
    def format_action(action_name: str) -> Text:
        """Format action name with appropriate styling"""
        return Text(action_name, style=Colors.ACTION)

    @staticmethod
    def format_good(good_name: str, quality: float = None) -> Text:
        """Format good name with appropriate styling"""
        if quality is not None:
            return Text(f"{good_name} (quality: {quality:.2f})", style=Colors.GOOD)
        return Text(good_name, style=Colors.GOOD)

    @staticmethod
    def format_need(need_name: str, value: float) -> Text:
        """Format need with appropriate styling"""
        return Text(f"{need_name}: {value:.2f}", style=Colors.NEED)

    @staticmethod
    def simulation_start(num_agents: int, max_days: int) -> None:
        """Print simulation start message"""
        text = Text()
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        text.append("Welcome to ", style="white")
        text.append("Mars Colony, 2993", style="bright_red")
        text.append("\n", style="white")
        text.append(f"Beginning simulation with ", style="white")
        text.append(f"{num_agents}", style=Colors.AGENT)
        text.append(" colonists for ", style="white")
        text.append(f"{max_days}", style=Colors.DAY)
        text.append(" days\n", style="white")
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        console.print(text)

    @staticmethod
    def simulation_end(num_days: int) -> None:
        """Print simulation end message"""
        text = Text()
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        text.append("Mars Colony simulation completed after ", style="white")
        text.append(f"{num_days}", style=Colors.DAY)
        text.append(" days\n", style="white")
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        console.print(text)

    @staticmethod
    def day_header(day: int) -> None:
        """Print day header"""
        text = Text()
        text.append("\n", style="white")
        text.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n", style="bright_white")
        text.append("┃ ", style="bright_white")
        text.append(f"DAY {day}", style=f"bold {Colors.DAY}")
        text.append(" " * (57 - len(f" DAY {day}")), style="white")
        text.append("┃\n", style="bright_white")
        text.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n", style="bright_white")
        console.print(text)

    @staticmethod
    def agent_rest(agent_name: str, rest_value: float) -> None:
        """Print agent rest action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" rested and recovered energy. ", style="white")
        text.append(f"Rest", style=Colors.NEED)
        text.append(": ", style="white")
        text.append(f"{rest_value:.2f}", style=Colors.NEED)
        console.print(text)

    @staticmethod
    def agent_work(agent_name: str, income: int, credits: float) -> None:
        """Print agent work action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" worked and earned ", style="white")
        text.append(f"{income}", style=Colors.CREDITS)
        text.append(" credits. Total: ", style="white")
        text.append(f"{credits:.0f}", style=Colors.CREDITS)
        console.print(text)

    @staticmethod
    def agent_harvest(agent_name: str, good_name: str, quality: float, food_level: float) -> None:
        """Print agent harvest action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" harvested ", style="white")
        text.append(f"{good_name}", style=Colors.GOOD)
        text.append(f" (quality: {quality:.2f})", style=Colors.GOOD)
        text.append(". ", style="white")
        text.append("Food", style=Colors.NEED)
        text.append(": ", style="white")
        text.append(f"{food_level:.2f}", style=Colors.NEED)
        console.print(text)

    @staticmethod
    def agent_craft(agent_name: str, item_name: str, item_type: str, quality: float, materials_cost: int) -> None:
        """Print agent craft action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" crafted ", style="white")
        text.append(f"{item_name}", style=Colors.GOOD)
        text.append(f" ({item_type}, quality: {quality:.2f})", style=Colors.GOOD)
        text.append(" using ", style="white")
        text.append(f"{materials_cost}", style=Colors.CREDITS)
        text.append(" credits of materials", style="white")
        console.print(text)

    @staticmethod
    def agent_sell(agent_name: str, good_name: str, good_type: str, quality: float, price: int) -> None:
        """Print agent sell action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" listed ", style="white")
        text.append(f"{good_name}", style=Colors.GOOD)
        text.append(f" ({good_type}, quality: {quality:.2f})", style=Colors.GOOD)
        text.append(" for sale at ", style="white")
        text.append(f"{price}", style=Colors.CREDITS)
        text.append(" credits", style="white")
        console.print(text)

    @staticmethod
    def agent_buy(agent_name: str, good_name: str, good_type: str, quality: float, price: int) -> None:
        """Print agent buy action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" bought ", style="white")
        text.append(f"{good_name}", style=Colors.GOOD)
        text.append(f" ({good_type}, quality: {quality:.2f})", style=Colors.GOOD)
        text.append(" for ", style="white")
        text.append(f"{price}", style=Colors.CREDITS)
        text.append(" credits", style="white")
        console.print(text)

    @staticmethod
    def agent_sale(agent_name: str, amount: int) -> None:
        """Print agent received credits from sale"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" received ", style="white")
        text.append(f"{amount}", style=Colors.CREDITS)
        text.append(" credits from sale", style="white")
        console.print(text)

    @staticmethod
    def agent_action(agent_name: str, action_type: str, reasoning: str = None) -> None:
        """Print agent action choice with reasoning"""
        text = Text()
        text.append("▶ ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" chose action ", style="white")
        text.append(action_type, style=Colors.ACTION)
        
        if reasoning and len(reasoning) > 2:
            # Truncate reasoning if too long
            max_length = 100
            if len(reasoning) > max_length:
                reasoning = reasoning[:max_length] + "..."
            
            text.append("\n  Reasoning: ", style="dim white")
            text.append(reasoning, style="dim white")
        
        console.print(text)

    @staticmethod
    def narrative_title(title: str) -> None:
        """Print narrative title"""
        text = Text()
        text.append("\n═══════ ", style="bright_white")
        text.append(title, style="bold bright_white")
        text.append(" ═══════\n", style="bright_white")
        console.print(text)

    @staticmethod
    def narrative_content(content: str) -> None:
        """Print narrative content with markdown rendering"""
        from rich.markdown import Markdown
        console.print(Markdown(content))

    @staticmethod
    def agent_death(agent_name: str, reason: str) -> None:
        """Print agent death message"""
        text = Text()
        text.append("☠️  ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" has died due to ", style="white")
        text.append(reason, style="bright_red")
        console.print(text)

    @staticmethod
    def deceased_good_added(good_name: str, agent_name: str, price: int) -> None:
        """Print message about deceased agent's good added to market"""
        text = Text()
        text.append("► Added ", style="white")
        text.append(good_name, style=Colors.GOOD)
        text.append(" from deceased ", style="white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" to market for ", style="white")
        text.append(f"{price}", style=Colors.CREDITS)
        text.append(" credits", style="white")
        console.print(text)

    @staticmethod
    def print_markdown(content: str) -> None:
        """Print content as markdown"""
        from rich.markdown import Markdown
        console.print(Markdown(content)) 