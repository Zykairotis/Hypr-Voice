# Helper Agent Usage Examples

This document provides practical examples of using the Helper Agent service for various use cases.

## Table of Contents

- [Basic Usage Examples](#basic-usage-examples)
- [Voice Agent Examples](#voice-agent-examples)
- [Content Processing Examples](#content-processing-examples)
- [Task Planning Examples](#task-planning-examples)
- [Claude SDK Integration Examples](#claude-sdk-integration-examples)
- [Web Application Examples](#web-application-examples)
- [Advanced Examples](#advanced-examples)

## Basic Usage Examples

### Simple Text Summarization

```python
from helper_agent import HelperAgent

async def basic_summarization():
    async with HelperAgent() as agent:
        # Summarize a long article
        article_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines,
        in contrast to the natural intelligence displayed by humans and animals.
        Leading AI textbooks define the field as the study of "intelligent agents":
        any device that perceives its environment and takes actions that maximize
        its chance of successfully achieving its goals...
        """

        result = await agent.summarize_text(
            text=article_text,
            max_length=200,
            focus="key_points"
        )

        print("Summary:", result["summary"])
        print("Compression ratio:", result["compression_ratio"])

# Run the example
asyncio.run(basic_summarization())
```

**Output:**
```
Summary: AI is machine intelligence that perceives environment and takes actions to achieve goals. It contrasts with natural intelligence shown by humans and animals. AI studies intelligent agents that maximize success chances in their environments.
Compression ratio: 0.15
```

### Content Analysis for Voice

```python
async def voice_content_analysis():
    async with HelperAgent() as agent:
        # Analyze technical content for voice delivery
        technical_content = """
        The microservices architecture pattern structures an application as a
        collection of loosely coupled, independently deployable services.
        Implementing this pattern requires careful consideration of service
        boundaries, inter-service communication, and data consistency.
        """

        result = await agent.analyze_content(
            content=technical_content,
            optimize_for_voice=True
        )

        print("Overall assessment:", result["analysis"]["overall_assessment"])
        print("\nVoice optimization suggestions:")
        for suggestion in result["voice_optimization"]["suggestions"]:
            print(f"- {suggestion}")

# Run the example
asyncio.run(voice_content_analysis())
```

**Output:**
```
Overall assessment: The content is well-structured but contains technical jargon that may be difficult for voice delivery.

Voice optimization suggestions:
- Break down long sentences for better spoken flow
- Define technical terms like "microservices" when first mentioned
- Use simpler language for complex concepts
- Add conversational transitions between ideas
```

### Task Breakdown

```python
async def task_planning_example():
    async with HelperAgent() as agent:
        # Plan a complex development task
        task_description = "Create a REST API for user authentication with JWT tokens"

        result = await agent.plan_task(
            task=task_description,
            max_steps=8,
            context="Web development project using Node.js and Express",
            complexity="medium"
        )

        print(f"Task: {result['original_task']}")
        print(f"Estimated time: {result['total_estimated_time_formatted']}")
        print(f"Quality score: {result['quality_score']}/100")
        print("\nSteps:")
        for step in result["steps"]:
            print(f"{step['step_number']}. {step['description']}")
            print(f"   Priority: {step['priority']}, Time: {step['estimated_time']}")

# Run the example
asyncio.run(task_planning_example())
```

**Output:**
```
Task: Create a REST API for user authentication with JWT tokens
Estimated time: 3 hours
Quality score: 88.0/100

Steps:
1. Design database schema for user authentication
   Priority: high, Time: 30 minutes
2. Set up Express.js project structure
   Priority: high, Time: 15 minutes
3. Install required dependencies (JWT, bcrypt, etc.)
   Priority: high, Time: 15 minutes
4. Implement user registration endpoint
   Priority: medium, Time: 45 minutes
5. Implement user login endpoint with JWT generation
   Priority: high, Time: 45 minutes
6. Create JWT middleware for protected routes
   Priority: high, Time: 30 minutes
7. Implement password reset functionality
   Priority: medium, Time: 30 minutes
8. Write comprehensive tests
   Priority: medium, Time: 30 minutes
```

## Voice Agent Examples

### Voice Command Processing

```python
class VoiceCommandProcessor:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def process_voice_command(self, command, context=None):
        """Process voice command and return optimized response."""
        async with self.helper_agent as agent:
            # Analyze the command
            analysis = await agent.analyze_content(
                content=command,
                optimize_for_voice=True
            )

            # Determine if it's a task or question
            if self.is_task_command(command):
                # Plan the task
                plan = await agent.plan_task(
                    task=command,
                    context=context
                )
                return self.format_voice_response_plan(command, plan)
            else:
                # Get answer or assistance
                response = await agent.bridge_to_claude_sdk(
                    request=command,
                    context=context,
                    voice_optimized=True
                )
                return response["voice_output"]

    def is_task_command(self, command):
        """Check if command is task-oriented."""
        task_indicators = ["help me", "create", "build", "implement", "set up", "make"]
        return any(indicator in command.lower() for indicator in task_indicators)

    def format_voice_response_plan(self, command, plan):
        """Format task plan for voice response."""
        response = f"I'll help you {command.lower()}. Here's the plan:\n\n"

        for step in plan["steps"][:5]:  # Limit to first 5 steps for voice
            response += f"Step {step['step_number']}: {step['description']}. "
            response += f"This should take about {step['estimated_time']}.\n"

        if plan["total_steps"] > 5:
            remaining = plan["total_steps"] - 5
            response += f"And {remaining} more steps. "
            response += f"The whole task should take about {plan['total_estimated_time_formatted']}."

        return response

# Usage example
async def process_voice_commands():
    processor = VoiceCommandProcessor()

    commands = [
        "Help me create a Python script for data analysis",
        "What's the difference between REST and GraphQL?",
        "Set up a development environment for React Native"
    ]

    for command in commands:
        print(f"\nCommand: {command}")
        response = await processor.process_voice_command(command)
        print(f"Response: {response}")

# Run the example
asyncio.run(process_voice_commands())
```

### Real-time Voice Optimization

```python
class RealTimeVoiceOptimizer:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.conversation_context = {}

    async def optimize_conversation_turn(self, user_input, session_id):
        """Optimize conversation turn for real-time voice interaction."""
        async with self.helper_agent as agent:
            # Get conversation context
            context = self.conversation_context.get(session_id, {})

            # Analyze user input
            analysis = await agent.analyze_content(
                content=user_input,
                optimize_for_voice=True
            )

            # Generate contextually appropriate response
            response = await agent.bridge_to_claude_sdk(
                request=user_input,
                context={
                    **context,
                    "voice_optimization": True,
                    "conversation_history": context.get("history", [])
                },
                voice_optimized=True
            )

            # Update conversation context
            self.conversation_context[session_id] = {
                "last_input": user_input,
                "last_response": response["response"],
                "history": context.get("history", []) + [
                    {"user": user_input, "assistant": response["voice_output"]}
                ],
                "session_age": context.get("session_age", 0) + 1
            }

            return {
                "optimized_response": response["voice_output"],
                "suggestions": analysis["voice_optimization"]["suggestions"],
                "context_updated": True
            }

# Usage example
async def simulate_conversation():
    optimizer = RealTimeVoiceOptimizer()
    session_id = "user123"

    conversation = [
        "Can you help me understand machine learning?",
        "What are the main types of machine learning algorithms?",
        "Can you give me a simple example of supervised learning?",
        "How do I get started with implementing this?"
    ]

    for i, user_input in enumerate(conversation):
        print(f"\nTurn {i+1}:")
        print(f"User: {user_input}")

        result = await optimizer.optimize_conversation_turn(user_input, session_id)

        print(f"Assistant: {result['optimized_response']}")
        if result['suggestions']:
            print(f"Voice suggestions: {', '.join(result['suggestions'][:2])}")

# Run the example
asyncio.run(simulate_conversation())
```

## Content Processing Examples

### Batch Content Processing

```python
import asyncio
from typing import List

class BatchContentProcessor:
    def __init__(self, max_concurrent=5):
        self.helper_agent = HelperAgent()
        self.max_concurrent = max_concurrent

    async def process_batch_summaries(self, texts: List[str], max_length=200):
        """Process multiple texts for summarization."""
        async with self.helper_agent as agent:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def process_single_text(text, index):
                async with semaphore:
                    result = await agent.summarize_text(
                        text=text,
                        max_length=max_length,
                        focus="key_points"
                    )
                    return {"index": index, "result": result}

            # Process all texts concurrently
            tasks = [
                process_single_text(text, i)
                for i, text in enumerate(texts)
            ]

            results = await asyncio.gather(*tasks)

            # Sort results by original index
            results.sort(key=lambda x: x["index"])

            return [r["result"] for r in results]

    async def analyze_content_collection(self, contents: List[str]):
        """Analyze a collection of content pieces."""
        async with self.helper_agent as agent:
            analyses = []

            for content in contents:
                analysis = await agent.analyze_content(
                    content=content,
                    optimize_for_voice=True
                )
                analyses.append(analysis)

            # Generate collection summary
            combined_text = "\n\n".join([
                f"Content {i+1}: {content}"
                for i, content in enumerate(contents)
            ])

            collection_summary = await agent.summarize_text(
                text=combined_text,
                max_length=500,
                focus="key_points"
            )

            return {
                "individual_analyses": analyses,
                "collection_summary": collection_summary,
                "total_contents": len(contents),
                "voice_optimization_needed": any(
                    a.get("voice_optimization", {}).get("status") == "needs_improvement"
                    for a in analyses
                )
            }

# Usage example
async def batch_processing_example():
    processor = BatchContentProcessor(max_concurrent=3)

    # Example texts for batch processing
    texts = [
        """
        Blockchain technology is a distributed ledger system that records transactions
        across multiple computers in a way that makes the resulting records immutable.
        It was originally devised for Bitcoin but has found applications in many fields.
        """,
        """
        Cloud computing provides on-demand availability of computer system resources,
        especially data storage and computing power, without direct active management
        by the user. It delivers computing services including servers, storage, databases,
        networking, and software over the Internet.
        """,
        """
        Artificial Intelligence (AI) refers to the simulation of human intelligence in
        machines that are programmed to think and learn. It encompasses machine learning,
        natural language processing, computer vision, and robotics.
        """
    ]

    # Process batch summaries
    print("Batch Summarization:")
    summaries = await processor.process_batch_summaries(texts, max_length=150)

    for i, summary in enumerate(summaries):
        print(f"\nText {i+1} Summary:")
        print(summary["summary"])
        print(f"Length: {summary['summary_length']} characters")

    # Analyze content collection
    print("\n\nCollection Analysis:")
    collection_analysis = await processor.analyze_content_collection(texts)
    print(f"Total contents: {collection_analysis['total_contents']}")
    print(f"Collection summary: {collection_analysis['collection_summary']['summary']}")
    print(f"Voice optimization needed: {collection_analysis['voice_optimization_needed']}")

# Run the example
asyncio.run(batch_processing_example())
```

### Content Enhancement Pipeline

```python
class ContentEnhancer:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def enhance_for_voice(self, content: str, target_audience="general"):
        """Enhance content for voice delivery."""
        async with self.helper_agent as agent:
            # Step 1: Analyze content
            analysis = await agent.analyze_content(
                content=content,
                optimize_for_voice=True
            )

            # Step 2: Get voice improvement suggestions
            improvements = await agent.suggest_voice_improvements(
                content=content,
                voice_style="conversational"
            )

            # Step 3: Generate improved version
            enhanced_version = improvements.get("improved_version", content)

            # Step 4: Create delivery notes
            delivery_notes = improvements.get("delivery_notes", [])

            # Step 5: Generate practice script
            practice_script = await self._create_practice_script(
                enhanced_version, delivery_notes
            )

            return {
                "original_content": content,
                "enhanced_content": enhanced_version,
                "analysis": analysis,
                "delivery_notes": delivery_notes,
                "practice_script": practice_script,
                "improvement_score": self._calculate_improvement_score(
                    content, enhanced_version
                )
            }

    async def _create_practice_script(self, content, delivery_notes):
        """Create a practice script with delivery notes."""
        script_parts = []
        sentences = content.split('. ')

        for i, sentence in enumerate(sentences):
            if sentence.strip():
                script_parts.append({
                    "sentence": sentence.strip() + '.',
                    "notes": [note for note in delivery_notes if i < len(delivery_notes)],
                    "practice_tip": self._get_practice_tip(sentence)
                })

        return script_parts

    def _get_practice_tip(self, sentence):
        """Get practice tip for a sentence."""
        if len(sentence) > 100:
            return "Take a breath before this long sentence"
        elif sentence.endswith('?'):
            return "Raise pitch slightly at the end"
        elif '!' in sentence:
            return "Add energy and enthusiasm"
        elif any(word in sentence.lower() for word in ['important', 'critical', 'essential']):
            return "Emphasize this word"
        else:
            return "Speak clearly and at a moderate pace"

    def _calculate_improvement_score(self, original, enhanced):
        """Calculate improvement score."""
        # Simple heuristic-based scoring
        original_issues = len([c for c in original if c.isupper()]) + original.count('(')
        enhanced_issues = len([c for c in enhanced if c.isupper()]) + enhanced.count('(')

        sentence_count_original = len(original.split('. '))
        sentence_count_enhanced = len(enhanced.split('. '))

        # Score based on reduced issues and better sentence structure
        issue_improvement = max(0, (original_issues - enhanced_issues) / max(original_issues, 1))
        sentence_improvement = min(0.2, abs(1 - sentence_count_enhanced/max(sentence_count_original, 1)))

        return min(100, int((issue_improvement + sentence_improvement) * 100))

# Usage example
async def content_enhancement_example():
    enhancer = ContentEnhancer()

    technical_content = """
    The implementation of microservices architecture necessitates careful consideration
    of service boundaries (DDD concepts), inter-service communication patterns (REST,
    gRPC, message queues), and data consistency strategies (saga pattern, event sourcing).
    Furthermore, containerization (Docker/Kubernetes) and CI/CD pipelines are essential
    for deployment and operational efficiency.
    """

    print("Original Content:")
    print(technical_content)

    result = await enhancer.enhance_for_voice(technical_content, target_audience="technical")

    print(f"\nEnhanced Content:")
    print(result["enhanced_content"])

    print(f"\nDelivery Notes:")
    for note in result["delivery_notes"]:
        print(f"- {note}")

    print(f"\nImprovement Score: {result['improvement_score']}/100")

    print("\nPractice Script:")
    for part in result["practice_script"][:3]:  # Show first 3 parts
        print(f"Sentence: {part['sentence']}")
        print(f"Tip: {part['practice_tip']}")
        print()

# Run the example
asyncio.run(content_enhancement_example())
```

## Task Planning Examples

### Project Planning Workflow

```python
class ProjectPlanner:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def plan_project(self, project_goal, project_context=None):
        """Create comprehensive project plan."""
        async with self.helper_agent as agent:
            # Step 1: Create high-level workflow
            workflow = await agent.create_workflow(
                goal=project_goal,
                context=project_context
            )

            # Step 2: Plan individual stages
            stage_plans = []
            for stage in workflow["stages"]:
                stage_plan = await agent.plan_task(
                    task=stage["description"],
                    context=project_context,
                    max_steps=5
                )
                stage_plans.append({
                    "stage": stage,
                    "plan": stage_plan
                })

            # Step 3: Create overall checklist
            checklist = await agent.create_checklist(
                process=f"Project: {project_goal}",
                detail_level="medium"
            )

            # Step 4: Generate risk assessment
            risk_assessment = await self._assess_risks(
                project_goal, stage_plans, agent
            )

            return {
                "project_goal": project_goal,
                "workflow": workflow,
                "stage_plans": stage_plans,
                "checklist": checklist,
                "risk_assessment": risk_assessment,
                "estimated_duration": workflow["estimated_duration"]
            }

    async def _assess_risks(self, goal, stage_plans, agent):
        """Assess project risks."""
        risk_areas = [
            "Technical complexity",
            "Resource requirements",
            "Timeline constraints",
            "Dependencies",
            "Integration challenges"
        ]

        risk_analysis = []
        for area in risk_areas:
            analysis = await agent.analyze_content(
                content=f"{goal} - {area} risk assessment",
                analysis_type="comprehensive"
            )
            risk_analysis.append({
                "area": area,
                "analysis": analysis,
                "risk_level": self._calculate_risk_level(analysis)
            })

        return risk_analysis

    def _calculate_risk_level(self, analysis):
        """Calculate risk level from analysis."""
        # Simple heuristic based on analysis content
        analysis_text = str(analysis).lower()

        high_risk_indicators = ["complex", "difficult", "challenging", "risk", "problem"]
        medium_risk_indicators = ["moderate", "some", "potential", "consider"]

        high_count = sum(1 for indicator in high_risk_indicators if indicator in analysis_text)
        medium_count = sum(1 for indicator in medium_risk_indicators if indicator in analysis_text)

        if high_count >= 2:
            return "high"
        elif medium_count >= 2 or high_count >= 1:
            return "medium"
        else:
            return "low"

# Usage example
async def project_planning_example():
    planner = ProjectPlanner()

    project_goal = "Build a customer support chatbot with AI capabilities"
    project_context = {
        "team_size": "3 developers",
        "timeline": "3 months",
        "technology_stack": "Python, React, OpenAI API",
        "budget": "moderate"
    }

    plan = await planner.plan_project(project_goal, project_context)

    print(f"Project: {plan['project_goal']}")
    print(f"Estimated Duration: {plan['estimated_duration']}")
    print(f"\nWorkflow Stages: {plan['workflow']['total_stages']}")

    print("\nStage Plans:")
    for stage_plan in plan["stage_plans"][:2]:  # Show first 2 stages
        stage = stage_plan["stage"]
        plan_data = stage_plan["plan"]
        print(f"\nStage {stage['stage_number']}: {stage['description']}")
        print(f"Duration: {stage['estimated_duration']}")
        print(f"Steps: {plan_data['total_steps']}")

    print("\nRisk Assessment:")
    for risk in plan["risk_assessment"]:
        print(f"{risk['area']}: {risk['risk_level'].upper()} risk")

    print(f"\nProject Checklist Items: {plan['checklist']['total_items']}")

# Run the example
asyncio.run(project_planning_example())
```

### Task Prioritization System

```python
class TaskManager:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.tasks = []

    async def add_task(self, task_description, priority_hint=None, deadline=None):
        """Add a new task to the system."""
        async with self.helper_agent as agent:
            # Analyze task complexity
            analysis = await agent.analyze_content(
                content=task_description,
                analysis_type="comprehensive"
            )

            task = {
                "id": len(self.tasks) + 1,
                "description": task_description,
                "priority_hint": priority_hint,
                "deadline": deadline,
                "complexity": analysis.get("metrics", {}),
                "created_at": datetime.now(),
                "status": "pending"
            }

            self.tasks.append(task)
            return task

    async def prioritize_tasks(self, criteria=None):
        """Prioritize all tasks based on criteria."""
        if criteria is None:
            criteria = ["urgency", "importance", "effort", "dependencies"]

        async with self.helper_agent as agent:
            task_descriptions = [task["description"] for task in self.tasks]

            prioritization = await agent.prioritize_tasks(
                tasks=task_descriptions,
                criteria=criteria
            )

            # Update tasks with priority information
            for prioritized_task in prioritization["prioritized_tasks"]:
                # Find matching task
                for task in self.tasks:
                    if self._tasks_match(task["description"], prioritized_task["description"]):
                        task["priority"] = prioritized_task["priority_score"]
                        task["rank"] = prioritized_task["rank"]
                        break

            return prioritization

    async def get_next_steps(self, current_state=""):
        """Get recommended next steps."""
        async with self.helper_agent as agent:
            completed_tasks = [
                task["description"] for task in self.tasks
                if task["status"] == "completed"
            ]

            pending_tasks = [
                task["description"] for task in self.tasks
                if task["status"] == "pending"
            ]

            if pending_tasks:
                goal = "Complete pending tasks efficiently"
                next_steps = await agent.suggest_next_steps(
                    current_state=current_state,
                    goal=goal,
                    completed_steps=completed_tasks
                )

                return next_steps
            else:
                return {"next_steps": [], "message": "No pending tasks"}

    def _tasks_match(self, task1, task2, threshold=0.8):
        """Check if two task descriptions match."""
        words1 = set(task1.lower().split())
        words2 = set(task2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union)
        return similarity >= threshold

# Usage example
async def task_management_example():
    manager = TaskManager()

    # Add tasks
    tasks_to_add = [
        ("Fix the authentication bug in production", "high", "2024-01-15"),
        ("Implement user profile page", "medium", "2024-01-20"),
        ("Write API documentation", "low", None),
        ("Optimize database queries", "high", "2024-01-18"),
        ("Set up CI/CD pipeline", "medium", "2024-01-25")
    ]

    print("Adding tasks...")
    for task_desc, priority, deadline in tasks_to_add:
        task = await manager.add_task(task_desc, priority, deadline)
        print(f"Added: {task['description']}")

    # Prioritize tasks
    print("\nPrioritizing tasks...")
    prioritization = await manager.prioritize_tasks()

    print("\nPrioritized Task List:")
    for task_info in prioritization["prioritized_tasks"]:
        print(f"{task_info['rank']}. {task_info['description']}")
        print(f"   Priority Score: {task_info['priority_score']:.1f}")

    # Get next steps
    print("\nGetting next steps...")
    next_steps = await manager.get_next_steps()

    if next_steps["next_steps"]:
        print("Recommended Next Steps:")
        for step in next_steps["next_steps"]:
            print(f"- {step['description']}")
    else:
        print(next_steps.get("message", "No next steps available"))

# Run the example
asyncio.run(task_management_example())
```

## Claude SDK Integration Examples

### Development Assistant Integration

```python
class DevelopmentAssistant:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.current_file = None
        self.project_context = {}

    async def assist_with_code(self, request, file_path=None, code_snippet=None):
        """Provide development assistance with Claude SDK bridge."""
        async with self.helper_agent as agent:
            # Build context
            context = {
                "application": "development",
                "task": "coding",
                "current_file": file_path,
                "code_snippet": code_snippet,
                "project_context": self.project_context
            }

            # Process request through Claude SDK bridge
            response = await agent.bridge_to_claude_sdk(
                request=request,
                context=context,
                voice_optimized=False  # Not voice-optimized for development
            )

            # Extract actionable items
            if response["actions"]:
                # Create task plan for implementation
                plan = await agent.plan_task(
                    task=response["actions"][0],
                    context=context,
                    max_steps=5
                )
                response["implementation_plan"] = plan

            return response

    async def explain_code(self, code, language="python"):
        """Explain code snippet."""
        request = f"Explain this {language} code: {code}"
        return await self.assist_with_code(request)

    async def suggest_improvements(self, code, language="python"):
        """Suggest code improvements."""
        request = f"Suggest improvements for this {language} code: {code}"
        return await self.assist_with_code(request)

    async def debug_issue(self, error_message, code_context=None):
        """Help debug an issue."""
        request = f"Help debug this error: {error_message}"
        return await self.assist_with_code(request, code_snippet=code_context)

# Usage example
async def development_assistant_example():
    assistant = DevelopmentAssistant()

    # Example 1: Explain code
    code_snippet = """
    def calculate_fibonacci(n):
        if n <= 1:
            return n
        else:
            return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    """

    print("Explaining code...")
    explanation = await assistant.explain_code(code_snippet, "python")
    print(f"Explanation: {explanation['response']}")

    # Example 2: Suggest improvements
    print("\nSuggesting improvements...")
    improvements = await assistant.suggest_improvements(code_snippet, "python")
    print(f"Improvements: {improvements['response']}")

    if improvements.get("implementation_plan"):
        plan = improvements["implementation_plan"]
        print(f"Implementation plan ({plan['total_steps']} steps):")
        for step in plan["steps"][:3]:
            print(f"  {step['step_number']}. {step['description']}")

    # Example 3: Debug issue
    print("\nDebugging issue...")
    error_msg = "RecursionError: maximum recursion depth exceeded"
    debug_help = await assistant.debug_issue(error_msg, code_snippet)
    print(f"Debug help: {debug_help['response']}")

# Run the example
asyncio.run(development_assistant_example())
```

### Voice-to-Code Translation

```python
class VoiceCodeTranslator:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def translate_voice_command(self, voice_input, context=None):
        """Translate voice input to executable code/command."""
        async with self.helper_agent as agent:
            # Step 1: Clean and preprocess voice input
            cleaned_input = self._clean_voice_input(voice_input)

            # Step 2: Translate to Claude SDK format
            translation = await agent.translate_voice_to_claude(
                voice_input=cleaned_input,
                intent="development",
                context_window=context
            )

            if translation["error"]:
                return translation

            # Step 3: Validate and format the command
            validated_command = await self._validate_command(
                translation["claude_command"],
                agent
            )

            # Step 4: Generate explanation
            explanation = await agent.analyze_content(
                content=f"Explain this command: {validated_command}",
                analysis_type="comprehensive"
            )

            return {
                "original_voice_input": voice_input,
                "cleaned_input": cleaned_input,
                "claude_command": validated_command,
                "explanation": explanation["analysis"]["overall_assessment"],
                "confidence": translation["translation_confidence"],
                "intent_analysis": translation["intent_analysis"]
            }

    def _clean_voice_input(self, voice_input):
        """Clean voice input for better processing."""
        import re

        # Remove filler words and normalize
        filler_words = ["um", "uh", "like", "you know", "actually", "basically"]
        cleaned = voice_input.lower()

        for filler in filler_words:
            cleaned = cleaned.replace(filler, "")

        # Clean up spacing and punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'[.!?]+', '.', cleaned)

        return cleaned

    async def _validate_command(self, command, agent):
        """Validate and format the command."""
        # Check if command is complete
        validation_prompt = f"""
        Is this command complete and actionable for a development environment?
        If not, make it complete: {command}
        """

        validation = await agent.generate_text(
            prompt=validation_prompt,
            max_tokens=200,
            temperature=0.2
        )

        return validation.strip() if validation else command

# Usage example
async def voice_code_translation_example():
    translator = VoiceCodeTranslator()

    voice_commands = [
        "Um, can you create a new Python file called main.py",
        "Like, I need to install the requests library",
        "Actually, could you help me set up a virtual environment",
        "You know, run the test suite for the project"
    ]

    for voice_cmd in voice_commands:
        print(f"\nVoice Input: '{voice_cmd}'")

        result = await translator.translate_voice_command(
            voice_cmd,
            context="Python development project"
        )

        print(f"Cleaned Input: '{result['cleaned_input']}'")
        print(f"Claude Command: {result['claude_command']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Confidence: {result['confidence']:.1%}")

# Run the example
asyncio.run(voice_code_translation_example())
```

## Web Application Examples

### FastAPI Service Integration

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from helper_agent import HelperAgent

app = FastAPI(title="Helper Agent API", version="1.0.0")

# Initialize helper agent
helper_agent = HelperAgent()

class Document(BaseModel):
    content: str
    title: Optional[str] = None
    metadata: Optional[dict] = {}

class SummarizeRequest(BaseModel):
    document: Document
    max_length: int = 500
    focus: str = "key_points"

class AnalyzeRequest(BaseModel):
    document: Document
    optimize_for_voice: bool = True
    analysis_type: str = "comprehensive"

class TaskPlanRequest(BaseModel):
    task: str
    context: Optional[str] = None
    max_steps: int = 10
    complexity: str = "medium"

class VoiceOptimizeRequest(BaseModel):
    content: str
    voice_style: str = "conversational"
    target_audience: str = "general"

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await helper_agent.initialize()
    print("Helper Agent service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await helper_agent.cleanup()
    print("Helper Agent service stopped")

# API Endpoints
@app.post("/summarize")
async def summarize_document(request: SummarizeRequest):
    """Summarize a document."""
    try:
        result = await helper_agent.summarize_text(
            text=request.document.content,
            max_length=request.max_length,
            focus=request.focus
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Add document metadata
        result["document_title"] = request.document.title
        result["document_metadata"] = request.document.metadata

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_document(request: AnalyzeRequest):
    """Analyze a document."""
    try:
        result = await helper_agent.analyze_content(
            content=request.document.content,
            optimize_for_voice=request.optimize_for_voice
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan-task")
async def plan_task(request: TaskPlanRequest):
    """Plan a task."""
    try:
        result = await helper_agent.plan_task(
            task=request.task,
            max_steps=request.max_steps,
            context=request.context
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize-voice")
async def optimize_for_voice(request: VoiceOptimizeRequest):
    """Optimize content for voice delivery."""
    try:
        # Get voice improvement suggestions
        improvements = await helper_agent.suggest_voice_improvements(
            content=request.content,
            voice_style=request.voice_style
        )

        if "error" in improvements:
            raise HTTPException(status_code=500, detail=improvements["error"])

        return JSONResponse(content=improvements)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-process")
async def batch_process_documents(
    documents: List[Document],
    operation: str = "summarize",
    max_length: int = 300
):
    """Process multiple documents in batch."""
    try:
        if operation == "summarize":
            # Process all documents concurrently
            tasks = [
                helper_agent.summarize_text(
                    text=doc.content,
                    max_length=max_length,
                    focus="key_points"
                )
                for doc in documents
            ]

            results = await asyncio.gather(*tasks)

            # Combine results with document info
            batch_results = []
            for i, (doc, result) in enumerate(zip(documents, results)):
                if "error" not in result:
                    result["document_title"] = doc.title
                    result["document_index"] = i
                    batch_results.append(result)

            return {
                "processed_documents": len(batch_results),
                "total_documents": len(documents),
                "results": batch_results
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported operation: {operation}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health = await helper_agent.health_check()
    return JSONResponse(content=health)

@app.get("/stats")
async def get_statistics():
    """Get service statistics."""
    stats = await helper_agent.get_stats()
    return JSONResponse(content=stats)

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### WebSocket Real-time Processing

```python
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.helper_agent = HelperAgent()

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Process message based on type
            response = await process_websocket_message(data, client_id)

            # Send response back to client
            await manager.send_personal_message(response, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def process_websocket_message(message: dict, client_id: str):
    """Process WebSocket message."""
    msg_type = message.get("type")
    data = message.get("data", {})
    request_id = message.get("request_id")

    try:
        if msg_type == "summarize":
            result = await manager.helper_agent.summarize_text(**data)
        elif msg_type == "analyze":
            result = await manager.helper_agent.analyze_content(**data)
        elif msg_type == "plan":
            result = await manager.helper_agent.plan_task(**data)
        elif msg_type == "voice_optimize":
            result = await manager.helper_agent.suggest_voice_improvements(**data)
        else:
            result = {"error": f"Unknown message type: {msg_type}"}

        return {
            "type": msg_type,
            "request_id": request_id,
            "data": result,
            "client_id": client_id,
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "type": "error",
            "request_id": request_id,
            "data": {"error": str(e)},
            "client_id": client_id,
            "timestamp": time.time()
        }
```

## Advanced Examples

### Multi-Modal Processing Pipeline

```python
class MultiModalProcessor:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def process_meeting_transcript(self, transcript, meeting_metadata=None):
        """Process meeting transcript and generate outputs."""
        async with self.helper_agent as agent:
            results = {}

            # Step 1: Generate executive summary
            results["executive_summary"] = await agent.summarize_text(
                text=transcript,
                max_length=300,
                focus="decisions"
            )

            # Step 2: Extract action items
            results["action_items"] = await agent.extract_key_information(
                text=transcript,
                information_types=["actions", "deadlines", "decisions"]
            )

            # Step 3: Create follow-up tasks
            if results["action_items"]["extracted_information"].get("actions"):
                actions = results["action_items"]["extracted_information"]["actions"]
                results["follow_up_plan"] = await agent.plan_task(
                    task=f"Complete action items from meeting: {', '.join(actions)}",
                    max_steps=len(actions) + 2,
                    context="Meeting follow-up"
                )

            # Step 4: Generate meeting minutes
            results["meeting_minutes"] = await agent.analyze_content(
                content=transcript,
                analysis_type="comprehensive"
            )

            # Step 5: Create voice briefing
            results["voice_briefing"] = await agent.suggest_voice_improvements(
                content=results["executive_summary"]["summary"],
                voice_style="professional"
            )

            return results

# Usage example
async def meeting_processing_example():
    processor = MultiModalProcessor()

    sample_transcript = """
    Meeting: Project Alpha Planning
    Date: January 15, 2024

    John: We need to decide on the technology stack for the new project.
    Sarah: I suggest React for frontend and Node.js for backend.
    Mike: What about the database? PostgreSQL would be good.
    John: Agreed. Sarah, can you create the project structure by Friday?
    Sarah: Yes, I'll set up the initial repository.
    Mike: I'll design the database schema.
    John: Great. Let's meet next Tuesday to review progress.
    """

    results = await processor.process_meeting_transcript(
        sample_transcript,
        {"meeting_type": "planning", "attendees": 3}
    )

    print("Executive Summary:")
    print(results["executive_summary"]["summary"])

    print("\nAction Items:")
    for action in results["action_items"]["extracted_information"].get("actions", []):
        print(f"- {action}")

    print("\nFollow-up Plan:")
    if results.get("follow_up_plan"):
        for step in results["follow_up_plan"]["steps"]:
            print(f"{step['step_number']}. {step['description']}")

    print("\nVoice Briefing:")
    print(results["voice_briefing"]["improved_version"])

# Run the example
asyncio.run(meeting_processing_example())
```

These examples demonstrate various ways to integrate and use the Helper Agent service across different applications and use cases. Each example shows practical implementation patterns that you can adapt to your specific needs.