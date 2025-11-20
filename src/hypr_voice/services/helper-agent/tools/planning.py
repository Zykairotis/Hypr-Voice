"""
Task Planning Tools for Helper Agent

This module provides task planning and breakdown capabilities optimized for voice workflows.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
import json
from datetime import datetime, timedelta

from ..sglang_client import SGLangClient

logger = logging.getLogger(__name__)


class PlanningTools:
    """
    Tools for task planning and breakdown optimized for voice agent workflows.

    Provides intelligent task decomposition with prioritization and time estimates.
    """

    def __init__(self, sglang_client: SGLangClient, prompts: Dict[str, Any]):
        """
        Initialize planning tools.

        Args:
            sglang_client: Initialized SGLang client
            prompts: Prompts configuration dictionary
        """
        self.sglang_client = sglang_client
        self.prompts = prompts.get("planning", {})

    async def plan_task(
        self,
        task: str,
        max_steps: int = 10,
        context: Optional[str] = None,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Break down a task into actionable steps.

        Args:
            task: Task to break down
            max_steps: Maximum number of steps to generate
            context: Additional context for planning
            complexity: Expected complexity ("simple", "medium", "complex")

        Returns:
            Dictionary containing task plan and steps.
        """
        try:
            if not task or not task.strip():
                return {"error": "No task provided for planning"}

            # Prepare planning messages
            messages = [
                {
                    "role": "system",
                    "content": self._get_planning_system_prompt(complexity)
                },
                {
                    "role": "user",
                    "content": self._format_planning_prompt(task, max_steps, context, complexity)
                }
            ]

            # Generate task plan
            plan_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1500,
                temperature=0.5  # Moderate temperature for creative planning
            )

            if not plan_result:
                return {"error": "Failed to generate task plan"}

            # Parse and structure the plan
            structured_plan = self._parse_task_plan(plan_result, max_steps)

            # Add metadata
            structured_plan.update({
                "original_task": task,
                "context": context,
                "complexity": complexity,
                "max_steps_requested": max_steps,
                "generated_at": datetime.now().isoformat()
            })

            # Calculate time estimates
            structured_plan = self._add_time_estimates(structured_plan)

            # Validate plan quality
            quality_score = self._validate_plan_quality(structured_plan)
            structured_plan["quality_score"] = quality_score

            return structured_plan

        except Exception as e:
            logger.error(f"Task planning failed: {e}")
            return {"error": f"Task planning failed: {str(e)}"}

    async def create_workflow(
        self,
        goal: str,
        stages: Optional[List[str]] = None,
        resources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a multi-stage workflow plan.

        Args:
            goal: Overall goal or objective
            stages: Optional predefined stages
            resources: Available resources and constraints

        Returns:
            Dictionary containing workflow plan.
        """
        try:
            if not goal or not goal.strip():
                return {"error": "No goal provided for workflow creation"}

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert project manager and workflow designer. Create comprehensive, actionable workflows with clear stages and dependencies."
                },
                {
                    "role": "user",
                    "content": self._format_workflow_prompt(goal, stages, resources)
                }
            ]

            workflow_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.4
            )

            if not workflow_result:
                return {"error": "Failed to generate workflow"}

            workflow = self._parse_workflow_result(workflow_result)

            # Add workflow metadata
            workflow.update({
                "goal": goal,
                "stages_provided": stages or [],
                "resources": resources or [],
                "created_at": datetime.now().isoformat(),
                "estimated_duration": self._estimate_workflow_duration(workflow)
            })

            return workflow

        except Exception as e:
            logger.error(f"Workflow creation failed: {e}")
            return {"error": f"Workflow creation failed: {str(e)}"}

    async def prioritize_tasks(
        self,
        tasks: List[str],
        criteria: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prioritize a list of tasks based on given criteria.

        Args:
            tasks: List of tasks to prioritize
            criteria: Prioritization criteria (urgency, importance, effort, dependencies)
            constraints: Any constraints or limitations

        Returns:
            Dictionary containing prioritized task list.
        """
        try:
            if not tasks:
                return {"error": "No tasks provided for prioritization"}

            if criteria is None:
                criteria = ["importance", "urgency", "effort", "dependencies"]

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in task management and prioritization. Analyze tasks and provide clear prioritization with reasoning."
                },
                {
                    "role": "user",
                    "content": self._format_prioritization_prompt(tasks, criteria, constraints)
                }
            ]

            prioritization_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1200,
                temperature=0.3  # Lower temperature for consistent prioritization
            )

            if not prioritization_result:
                return {"error": "Failed to prioritize tasks"}

            prioritized_tasks = self._parse_prioritization_result(prioritization_result, tasks)

            return {
                "original_tasks": tasks,
                "prioritized_tasks": prioritized_tasks,
                "criteria_used": criteria,
                "constraints": constraints,
                "total_tasks": len(tasks)
            }

        except Exception as e:
            logger.error(f"Task prioritization failed: {e}")
            return {"error": f"Task prioritization failed: {str(e)}"}

    async def suggest_next_steps(
        self,
        current_state: str,
        goal: str,
        completed_steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Suggest next logical steps based on current state and goal.

        Args:
            current_state: Description of current situation
            goal: Desired end goal
            completed_steps: List of already completed steps

        Returns:
            Dictionary containing next step suggestions.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in project planning and execution. Analyze the current state and suggest logical next steps to achieve the goal."
                },
                {
                    "role": "user",
                    "content": self._format_next_steps_prompt(current_state, goal, completed_steps)
                }
            ]

            next_steps_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.4
            )

            if not next_steps_result:
                return {"error": "Failed to generate next steps"}

            next_steps = self._parse_next_steps(next_steps_result)

            return {
                "current_state": current_state,
                "goal": goal,
                "completed_steps": completed_steps or [],
                "next_steps": next_steps,
                "progress_percentage": self._calculate_progress(completed_steps, next_steps)
            }

        except Exception as e:
            logger.error(f"Next steps suggestion failed: {e}")
            return {"error": f"Next steps suggestion failed: {str(e)}"}

    async def create_checklist(
        self,
        process: str,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a comprehensive checklist for a process.

        Args:
            process: Process or procedure to create checklist for
            detail_level: Level of detail ("brief", "medium", "detailed")

        Returns:
            Dictionary containing checklist.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert in process documentation. Create clear, comprehensive checklists with {detail_level} level of detail."
                },
                {
                    "role": "user",
                    "content": f"Create a {detail_level} checklist for: {process}"
                }
            ]

            checklist_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1000,
                temperature=0.2  # Low temperature for consistency
            )

            if not checklist_result:
                return {"error": "Failed to generate checklist"}

            checklist = self._parse_checklist_result(checklist_result, detail_level)

            return {
                "process": process,
                "checklist": checklist,
                "detail_level": detail_level,
                "total_items": len(checklist),
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Checklist creation failed: {e}")
            return {"error": f"Checklist creation failed: {str(e)}"}

    def _get_planning_system_prompt(self, complexity: str) -> str:
        """Get system prompt for task planning."""
        base_prompt = self.prompts.get("system",
            "You are a task planning expert that breaks down complex tasks into actionable steps.")

        complexity_prompts = {
            "simple": " Break down the task into basic, straightforward steps.",
            "medium": " Break down the task into clear, logical steps with appropriate detail.",
            "complex": " Break down the task into detailed, manageable subtasks with dependencies and considerations."
        }

        if complexity in complexity_prompts:
            base_prompt += complexity_prompts[complexity]

        return base_prompt

    def _format_planning_prompt(self, task: str, max_steps: int, context: Optional[str], complexity: str) -> str:
        """Format the planning prompt."""
        template = self.prompts.get("user_template",
            "Break down the following task into clear, actionable steps:\n\n{task}\n\nPlan:")

        prompt = template.format(task=task)

        prompt += f"\n\nPlease provide exactly {max_steps} steps or fewer."
        prompt += f"\nTask complexity: {complexity}"

        if context:
            prompt += f"\n\nAdditional context: {context}"

        prompt += "\n\nFor each step, include:\n1. Clear action description\n2. Estimated time\n3. Priority level\n4. Dependencies"

        return prompt

    def _parse_task_plan(self, plan_result: str, max_steps: int) -> Dict[str, Any]:
        """Parse and structure the task plan result."""
        steps = self._extract_steps_from_text(plan_result)

        # Limit to requested number of steps
        steps = steps[:max_steps]

        # Add structure to each step
        structured_steps = []
        for i, step in enumerate(steps, 1):
            structured_step = {
                "step_number": i,
                "description": step.get("description", ""),
                "priority": step.get("priority", "medium"),
                "estimated_time": step.get("time", "15 minutes"),
                "dependencies": step.get("dependencies", []),
                "notes": step.get("notes", "")
            }
            structured_steps.append(structured_step)

        return {
            "steps": structured_steps,
            "total_steps": len(structured_steps),
            "raw_plan": plan_result
        }

    def _extract_steps_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured steps from text."""
        steps = []

        # Try different step patterns
        patterns = [
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',  # Numbered list
            r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)',  # Bullet points
            r'Step\s*(\d+):\s*(.+?)(?=Step\s*\d+|$)',  # "Step X:" format
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches and len(matches) > 1:  # Found multiple steps
                for match in matches:
                    if isinstance(match, tuple):
                        step_text = match[1] if len(match) > 1 else match[0]
                    else:
                        step_text = match

                    # Parse step details
                    step_info = self._parse_single_step(step_text.strip())
                    steps.append(step_info)

                if steps:  # If we found steps, break
                    break

        # If no structured steps found, create simple steps from paragraphs
        if not steps:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for i, paragraph in enumerate(paragraphs[:10]):  # Limit to 10 paragraphs
                steps.append({
                    "description": paragraph,
                    "priority": "medium",
                    "time": "15 minutes"
                })

        return steps

    def _parse_single_step(self, step_text: str) -> Dict[str, Any]:
        """Parse individual step information."""
        step_info = {"description": step_text}

        # Look for priority indicators
        priority_patterns = [
            r'(?:priority|urgency):\s*(high|medium|low)',
            r'\[(high|medium|low)\]',
            r'\*\*(high|medium|low)\*\*'
        ]

        for pattern in priority_patterns:
            match = re.search(pattern, step_text, re.IGNORECASE)
            if match:
                step_info["priority"] = match.group(1).lower()
                break

        # Look for time estimates
        time_patterns = [
            r'(?:time|duration|estimate):\s*(.+?)(?:\n|$)',
            r'\((\d+\s*(?:minutes?|hours?|days?))\)',
            r'(~|\.)\s*(\d+\s*(?:minutes?|hours?|days?))'
        ]

        for pattern in time_patterns:
            match = re.search(pattern, step_text, re.IGNORECASE)
            if match:
                step_info["time"] = match.group(1).strip()
                break

        # Look for dependencies
        dep_patterns = [
            r'(?:depends? on|requires?|after):\s*(.+?)(?:\n|$)',
            r'→\s*(.+)'
        ]

        for pattern in dep_patterns:
            match = re.search(pattern, step_text, re.IGNORECASE)
            if match:
                dependencies = [dep.strip() for dep in re.split(r'[,;]', match.group(1))]
                step_info["dependencies"] = dependencies
                break

        return step_info

    def _add_time_estimates(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Add time estimates to plan if not present."""
        total_time = 0

        for step in plan["steps"]:
            if "estimated_time" not in step or not step["estimated_time"]:
                # Default time estimate based on complexity
                step["estimated_time"] = "15 minutes"

            # Parse time and convert to minutes
            time_minutes = self._parse_time_to_minutes(step["estimated_time"])
            step["time_minutes"] = time_minutes
            total_time += time_minutes

        plan["total_estimated_time"] = total_time
        plan["total_estimated_time_formatted"] = self._format_minutes_to_human(total_time)

        return plan

    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Parse time string to minutes."""
        time_str = time_str.lower().strip()

        # Handle various time formats
        patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*hours?',
            r'(\d+)\s*days?',
            r'(\d+)\s*mins?',
            r'(\d+)\s*hrs?',
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str)
            if match:
                value = int(match.group(1))
                if "hour" in pattern or "hr" in pattern:
                    return value * 60
                elif "day" in pattern:
                    return value * 60 * 8  # 8-hour workday
                else:
                    return value

        return 15  # Default to 15 minutes

    def _format_minutes_to_human(self, minutes: int) -> str:
        """Format minutes to human-readable string."""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 480:  # Less than 8 hours
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins else f"{hours} hours"
        else:
            days = minutes // (8 * 60)
            hours = (minutes % (8 * 60)) // 60
            return f"{days}d {hours}h" if hours else f"{days} days"

    def _validate_plan_quality(self, plan: Dict[str, Any]) -> float:
        """Validate the quality of the generated plan."""
        score = 0.0
        max_score = 100.0

        steps = plan.get("steps", [])

        # Check number of steps (should be reasonable)
        if 3 <= len(steps) <= 10:
            score += 20
        elif 1 <= len(steps) < 3:
            score += 10

        # Check if steps have clear descriptions
        clear_steps = sum(1 for step in steps if len(step.get("description", "")) > 10)
        if steps:
            score += (clear_steps / len(steps)) * 30

        # Check if steps have priorities
        prioritized_steps = sum(1 for step in steps if step.get("priority"))
        if steps:
            score += (prioritized_steps / len(steps)) * 20

        # Check if steps have time estimates
        timed_steps = sum(1 for step in steps if step.get("estimated_time"))
        if steps:
            score += (timed_steps / len(steps)) * 20

        # Check for logical flow (simple heuristic)
        logical_flow_score = self._check_logical_flow(steps)
        score += logical_flow_score * 10

        return min(score, max_score)

    def _check_logical_flow(self, steps: List[Dict[str, Any]]) -> float:
        """Check if steps have logical flow."""
        if len(steps) < 2:
            return 0.5

        # Simple heuristic: check for common logical progression keywords
        logical_indicators = [
            "first", "then", "next", "after", "before", "once", "when", "begin", "start",
            "continue", "proceed", "finally", "complete", "finish", "end"
        ]

        logical_count = 0
        for step in steps:
            description = step.get("description", "").lower()
            if any(indicator in description for indicator in logical_indicators):
                logical_count += 1

        return logical_count / len(steps) if steps else 0

    def _format_workflow_prompt(self, goal: str, stages: Optional[List[str]], resources: Optional[List[str]]) -> str:
        """Format workflow creation prompt."""
        prompt = f"Create a comprehensive workflow plan for: {goal}\n\n"

        if stages:
            prompt += f"Include these stages: {', '.join(stages)}\n"

        if resources:
            prompt += f"Available resources: {', '.join(resources)}\n"

        prompt += "\nProvide:\n1. Clear stages with descriptions\n2. Key activities in each stage\n3. Dependencies between stages\n4. Milestones and deliverables\n5. Timeline estimates"

        return prompt

    def _parse_workflow_result(self, workflow_text: str) -> Dict[str, Any]:
        """Parse workflow creation result."""
        stages = self._extract_workflow_stages(workflow_text)

        return {
            "stages": stages,
            "raw_workflow": workflow_text,
            "total_stages": len(stages)
        }

    def _extract_workflow_stages(self, text: str) -> List[Dict[str, Any]]:
        """Extract stages from workflow text."""
        stages = []

        # Look for stage patterns
        stage_patterns = [
            r'(?:Stage|Phase)\s*(\d+):\s*(.+?)(?=(?:Stage|Phase)\s*\d+|$)',
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',
        ]

        for pattern in stage_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    stage_num = match[0] if isinstance(match, tuple) else str(len(stages) + 1)
                    stage_content = match[1] if isinstance(match, tuple) else match

                    stage = {
                        "stage_number": stage_num,
                        "description": stage_content.strip(),
                        "activities": self._extract_activities(stage_content),
                        "estimated_duration": self._extract_duration(stage_content)
                    }
                    stages.append(stage)

                if stages:
                    break

        return stages

    def _extract_activities(self, stage_text: str) -> List[str]:
        """Extract activities from stage text."""
        activities = []

        # Look for bullet points or numbered lists within stage text
        activity_patterns = [
            r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)',
            r'\d+\.\s*(.+?)(?=\d+\.|\n\n|$)'
        ]

        for pattern in activity_patterns:
            matches = re.findall(pattern, stage_text, re.DOTALL)
            if matches:
                activities.extend([match.strip() for match in matches if len(match.strip()) > 5])
                break

        return activities[:5]  # Limit to 5 activities per stage

    def _extract_duration(self, stage_text: str) -> str:
        """Extract duration from stage text."""
        duration_patterns = [
            r'(?:duration|time|estimate):\s*(.+?)(?:\n|$)',
            r'\((\d+\s*(?:days?|weeks?|months?))\)',
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, stage_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "TBD"

    def _estimate_workflow_duration(self, workflow: Dict[str, Any]) -> str:
        """Estimate total workflow duration."""
        stages = workflow.get("stages", [])
        total_days = 0

        for stage in stages:
            duration = stage.get("estimated_duration", "")
            days = self._parse_duration_to_days(duration)
            total_days += days

        if total_days == 0:
            return "TBD"
        elif total_days < 7:
            return f"{total_days} days"
        elif total_days < 30:
            weeks = total_days // 7
            days = total_days % 7
            return f"{weeks} weeks" if days == 0 else f"{weeks} weeks {days} days"
        else:
            months = total_days // 30
            weeks = (total_days % 30) // 7
            return f"{months} months" if weeks == 0 else f"{months} months {weeks} weeks"

    def _parse_duration_to_days(self, duration_str: str) -> int:
        """Parse duration string to days."""
        if not duration_str or duration_str == "TBD":
            return 0

        duration_str = duration_str.lower()

        patterns = [
            (r'(\d+)\s*days?', 1),
            (r'(\d+)\s*weeks?', 7),
            (r'(\d+)\s*months?', 30),
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, duration_str)
            if match:
                return int(match.group(1)) * multiplier

        return 0

    def _format_prioritization_prompt(self, tasks: List[str], criteria: List[str], constraints: Optional[str]) -> str:
        """Format prioritization prompt."""
        prompt = f"Prioritize these tasks based on {', '.join(criteria)}:\n\n"

        for i, task in enumerate(tasks, 1):
            prompt += f"{i}. {task}\n"

        prompt += f"\nCriteria: {', '.join(criteria)}"

        if constraints:
            prompt += f"\n\nConstraints: {constraints}"

        prompt += "\n\nProvide:\n1. Ranked list of tasks\n2. Reasoning for each prioritization\n3. Suggested execution order"

        return prompt

    def _parse_prioritization_result(self, result_text: str, original_tasks: List[str]) -> List[Dict[str, Any]]:
        """Parse prioritization result."""
        prioritized = []

        # Look for numbered lists or rankings
        patterns = [
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',
            r'Rank\s*(\d+):\s*(.+?)(?=Rank\s*\d+|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, result_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    rank = int(match[0]) if match[0].isdigit() else len(prioritized) + 1
                    task_info = match[1].strip()

                    # Find matching original task
                    matched_task = self._find_matching_task(task_info, original_tasks)

                    prioritized.append({
                        "rank": rank,
                        "task": matched_task,
                        "reasoning": task_info,
                        "priority_score": max(100 - rank * 10, 10)  # Simple scoring
                    })

                if prioritized:
                    break

        return prioritized

    def _find_matching_task(self, task_info: str, original_tasks: List[str]) -> str:
        """Find the best matching original task."""
        task_info_lower = task_info.lower()

        # Look for exact or partial matches
        for task in original_tasks:
            if task.lower() in task_info_lower or task_info_lower in task.lower():
                return task

        # If no match found, return the task info as is
        return task_info[:100] + "..." if len(task_info) > 100 else task_info

    def _format_next_steps_prompt(self, current_state: str, goal: str, completed_steps: Optional[List[str]]) -> str:
        """Format next steps prompt."""
        prompt = f"Current state: {current_state}\n\n"
        prompt += f"Goal: {goal}\n\n"

        if completed_steps:
            prompt += f"Completed steps:\n"
            for step in completed_steps:
                prompt += f"✓ {step}\n"
            prompt += "\n"

        prompt += "Suggest the next 3-5 logical steps to achieve the goal. "
        prompt += "For each suggestion, explain why it's the right next step."

        return prompt

    def _parse_next_steps(self, result_text: str) -> List[Dict[str, Any]]:
        """Parse next steps result."""
        next_steps = []

        # Extract numbered or bulleted suggestions
        patterns = [
            r'(?:Next\s+)?Step\s*(\d+):\s*(.+?)(?=(?:Next\s+)?Step\s*\d+|$)',
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',
            r'[-•]\s*(.+?)(?=[-•]|\n\n|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, result_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    step_num = match[0] if isinstance(match, tuple) else str(len(next_steps) + 1)
                    step_desc = match[1] if isinstance(match, tuple) else match

                    next_steps.append({
                        "step_number": int(step_num) if step_num.isdigit() else len(next_steps) + 1,
                        "description": step_desc.strip(),
                        "reasoning": self._extract_reasoning(step_desc)
                    })

                if next_steps:
                    break

        return next_steps[:5]  # Limit to 5 next steps

    def _extract_reasoning(self, step_text: str) -> str:
        """Extract reasoning from step text."""
        # Look for reasoning keywords
        reasoning_patterns = [
            r'(?:because|since|as|reason):\s*(.+?)(?:\n|$)',
            r'\(([^)]+)\)',
        ]

        for pattern in reasoning_patterns:
            match = re.search(pattern, step_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _calculate_progress(self, completed_steps: Optional[List[str]], next_steps: List[Dict[str, Any]]) -> float:
        """Calculate progress percentage."""
        if not completed_steps and not next_steps:
            return 0.0

        completed = len(completed_steps) if completed_steps else 0
        remaining = len(next_steps)

        if completed == 0 and remaining == 0:
            return 0.0

        # Simple progress calculation
        total = completed + remaining
        return (completed / total) * 100 if total > 0 else 0.0

    def _parse_checklist_result(self, checklist_text: str, detail_level: str) -> List[Dict[str, Any]]:
        """Parse checklist result."""
        checklist_items = []

        # Extract checklist items
        patterns = [
            r'\[([ x✓])\]\s*(.+?)(?=\n\[|$)',  # Checkbox format
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',  # Numbered list
            r'[-•]\s*(.+?)(?=[-•]|\n\n|$)',  # Bullet points
        ]

        for pattern in patterns:
            matches = re.findall(pattern, checklist_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        status = match[0] if len(match) > 1 else ""
                        item_text = match[1] if len(match) > 1 else match[0]
                    else:
                        status = ""
                        item_text = match

                    checklist_items.append({
                        "description": item_text.strip(),
                        "completed": status.lower() in ['x', '✓'],
                        "category": self._categorize_checklist_item(item_text)
                    })

                if checklist_items:
                    break

        return checklist_items

    def _categorize_checklist_item(self, item_text: str) -> str:
        """Categorize checklist item."""
        item_lower = item_text.lower()

        categories = {
            "preparation": ["prepare", "setup", "configure", "install", "gather"],
            "execution": ["execute", "run", "perform", "implement", "complete"],
            "verification": ["check", "verify", "test", "validate", "review"],
            "cleanup": ["cleanup", "close", "finalize", "document", "save"]
        }

        for category, keywords in categories.items():
            if any(keyword in item_lower for keyword in keywords):
                return category

        return "general"