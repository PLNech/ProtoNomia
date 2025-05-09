"""
ProtoNomia Scribe
A utility class for rich console output formatting using cyberpunk colors.
"""
import re
from copy import deepcopy
from typing import Any

from rich.console import Console
from rich.status import Status
from rich.text import Text

from src.models import SimulationState, Agent, AgentAction, AgentActionResponse, Song


def rich_replace(text: str, old: str, new: Text) -> Text:
    parts = text.split(old)
    result = Text()
    for i, part in enumerate(parts):
        result.append(part)
        if i < len(parts) - 1:
            result.append(new)
    return result


# Initialize rich console
console = Console()


# Cyberpunk color scheme
class Colors:
    """Cyberpunk color scheme for rich text output"""
    AGENT = "bright_magenta"  # Neon Pink for agent names
    CREDITS = "bright_green"  # Neon Green for credits
    ACTION = "dark_orange"  # Neon Orange for actions
    ACTION_EXTRA = "gold3"  # Brighter Orange for extras
    GOOD = "bright_blue"  # Neon Blue for goods
    NEED = "purple"  # Neon Purple for needs
    NEED_LOW = "purple4"  # Darker Purple for needs
    HIGHLIGHT = "bright_white"  # White for highlights
    DAY = "bright_red"  # Red for day markers
    NARRATIVE = "white"  # Default for narrative text
    STATUS = "cyan1" # Cyan for status indicators


class Scribe:
    """
    The Scribe is responsible for all rich text output in the simulation.
    It formats and colorizes output for better readability and aesthetic.
    """

    # Add class-level status attribute
    _status = None

    @classmethod
    def print(cls, text: str, style: str = None) -> None:
        """Print text with optional style"""
        if style:
            console.print(text, style=style)
        else:
            console.print(text)

    @classmethod
    def status(cls, message, spinner="dots"):
        """
        Create and display a status indicator with spinner.
        Returns the status object that can be used as a context manager.

        Args:
            message: The status message to display
            spinner: Name of the spinner animation

        Returns:
            Status: A Rich Status object that can be used as a context manager
        """
        # If there's an existing status, stop it
        if cls._status is not None:
            cls._status.stop()

        # Create status text with cyberpunk styling
        status_text = Text()
        status_text.append("⚡ ", style="bright_yellow")
        status_text.append(message, style=Colors.STATUS)

        # Create and start the status
        cls._status = Status(
            status_text,
            console=console,
            spinner=spinner,
            spinner_style="bright_cyan",
            speed=1.5
        )
        cls._status.start()
        return cls._status

    @classmethod
    def stop_status(cls):
        """Stop the current status indicator if one exists."""
        if cls._status is not None:
            cls._status.stop()
            cls._status = None

    @staticmethod
    def format_agent(agent_name: str) -> Text:
        """Format an agent name with appropriate styling"""
        return Text(agent_name, style=Colors.AGENT)

    @staticmethod
    def format_credits(amount: float) -> Text:
        """Format credit amount with appropriate styling"""
        return Text(f"{amount:.0f}", style=Colors.CREDITS)

    @staticmethod
    def format_action(action: AgentAction) -> Text:
        """Format action name with appropriate styling"""
        # Let's add the extras when present in a separate color
        if action.extras:
            return Text(f"{action.type.value}", style=Colors.ACTION) \
                + Text(" (", style=Colors.NARRATIVE) \
                + Text(f"{str(action.extras):50}", style=Colors.ACTION_EXTRA) \
                + Text(")", style=Colors.NARRATIVE)
        return Text(str(action.type.value), style=Colors.ACTION)

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
        text.append("Mars Settlement, 2993", style="bright_red")
        text.append("\n", style="white")
        text.append(f"Beginning simulation with ", style="white")
        text.append(f"{num_agents}", style=Colors.AGENT)
        text.append(" citizens for ", style="white")
        text.append(f"{max_days}", style=Colors.DAY)
        text.append(" days\n", style="white")
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        console.print(text)

    @staticmethod
    def simulation_end(num_days: int) -> None:
        """Print simulation end message"""
        text = Text()
        text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_white")
        text.append("Mars Settlement simulation completed after ", style="white")
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
    def agent_created(agent: Agent) -> None:
        """Print agent created message"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent.name, style=Colors.AGENT)
        text.append(" just spawned! Personality: ", style="white")
        # italicize the personality text
        text.append(f"{agent.personality.text}", style="white")
        text.append(", needs: ", style="white")
        text.append(str(agent.needs), style=Colors.NEED)
        if len(agent.goods) > 0:
            text.append(", and goods: ", style="white")
            text.append(", ".join([str(g) for g in agent.goods]), style=Colors.GOOD)
        else:
            text.append(", and empty pockets.", style="white")

        console.print(text)

    @staticmethod
    def agent_eat(agent_name: str, food_name: str, updated, amount: float) -> None:
        """Print agent eat automatic action."""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" was hungry and ate ", style="white")
        text.append(f"{food_name}", style=Colors.GOOD)
        text.append(": ", style="white")
        text.append(f"{updated - amount:.2f}", style=Colors.NEED_LOW)
        text.append(" -> ", style="white")
        text.append(f"{updated:.2f}", style=Colors.NEED)
        console.print(text)

    @staticmethod
    def agent_rest(agent_name: str, updated: float, amount: float) -> None:
        """Print agent rest action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" rested and recovered energy. ", style="white")
        text.append(f"Rest", style=Colors.NEED)
        text.append(": ", style="white")
        text.append(f"{updated - amount:.2f}", style=Colors.NEED_LOW)
        text.append(" -> ", style="white")
        text.append(f"{updated:.2f}", style=Colors.NEED)
        console.print(text)

    @staticmethod
    def agent_think(agent_name: str, thoughts: str, extras: dict[str, Any] = None) -> None:
        """Print agent rest action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" spent the day thinking: ", style="white")
        text.append(f"{thoughts}", style=Colors.HIGHLIGHT)
        if extras:
            extras = deepcopy(extras)
            del extras["thoughts"]
            text.append("(", style="bright_white")
            text.append(repr(f"{extras}"), style=Colors.GOOD)
            text.append(")", style="bright_white")

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
    def agent_song(agent_name: str, song: Song, extras: dict[str, Any] = None) -> None:
        # agent.name, song, extras
        # RENDER COLORFUL METADATA VIA: o COMPOSE ({'title': 'Red Planet Serenade', 'genre':
        # 'Synthwave', 'bpm': 128, 'tags': ['space', 'nostalgic', 'futuristic'], 'description': 'A melodic journey through the Martian landscapes.'})
        """Print agent rest action"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" spent the day composing a new ", style=Colors.NARRATIVE)
        text.append(f"{song.genre}", style=Colors.GOOD)
        text.append(" song : ", style=Colors.NARRATIVE)
        text.append(f"{song.title} ", style=Colors.HIGHLIGHT)
        text.append("[", style=Colors.NARRATIVE)
        text.append(f"{song.bpm}", style=Colors.CREDITS)
        text.append(" BPM]\n", style=Colors.NARRATIVE)

        if song.tags:
            text.append("[", style=Colors.NARRATIVE)
            text.append(', '.join(song.tags), style=Colors.AGENT)
            text.append("]", style=Colors.NARRATIVE)

        if song.description:
            text.append(f"{song.description}\n", style=Colors.NARRATIVE)

        # if extras:
        #     extras = deepcopy(extras)
        #     del extras["thoughts"]
        #     text.append("(", style="bright_white")
        #     text.append(repr(f"{extras}"), style=Colors.GOOD)
        #     text.append(")", style="bright_white")

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
    def agent_sale(agent_name: str, amount: float) -> None:
        """Print agent received credits from sale"""
        text = Text()
        text.append("► ", style="bright_white")
        text.append(agent_name, style=Colors.AGENT)
        text.append(" received ", style="white")
        text.append(f"{amount}", style=Colors.CREDITS)
        text.append(" credits from sale", style="white")
        console.print(text)

    @staticmethod
    def agent_action(agent: Agent, action: (AgentAction, AgentActionResponse)) -> None:
        """Print agent action choice with reasoning"""
        text = Text()
        text.append("\n▶ ", style="bright_white")
        text.append(agent.name, style=Colors.AGENT)
        text.append("(", style="bright_white")
        text.append(repr(agent.needs), style=Colors.NEED)
        text.append(")[", style="bright_white")
        text.append(f"{agent.credits:.2f}", style=Colors.CREDITS)
        text.append(" credits]", style="bright_white")
        text.append(" chose to ", style="white")
        text.append(Scribe.format_action(action))

        if action.reasoning and len(action.reasoning) > 2:
            reasoning = deepcopy(action.reasoning)
            max_length = 200
            if len(action.reasoning) > max_length:
                reasoning = action.reasoning[:max_length] + "..."

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
    def narrative_content(content: str, state: SimulationState) -> None:
        """Print narrative content with markdown rendering"""
        lines = content.split('\n')
        all_agent_names = []
        # Identify agent names and highlight in the narrative
        # TODO: Same for goods names
        for agent in state.agents:
            all_agent_names.append(agent.name)
            if len(agent.name.split(' ')) == 2:
                all_agent_names.append(agent.name.split(' ')[0])
                all_agent_names.append(agent.name.split(' ')[1])
        for line in lines:
            expression_any_agent_name = r'\b(' + '|'.join(re.escape(name) for name in all_agent_names) + r')\b'
            matches = re.findall(expression_any_agent_name, line)
            if matches:
                for match in matches:
                    line = line.replace(match, f"[{Colors.AGENT}]{match}[/{Colors.AGENT}]")
            console.print(line, style=Colors.NARRATIVE)

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

    @staticmethod
    def set_loading(is_loading: bool = True) -> None:
        pass
