# Hypr-Voice Enhanced Mode Setup Guide

## 🚀 Overview
Your Hypr-Voice system now supports **two modes** with context-aware transcription using your SG-Lang Qwen3 1.7B server.

## 🎹 Key Bindings

### **F9** - Raw Mode (Default)
- **Fast**: Instant transcription and paste
- **Basic**: No AI processing
- **Use for**: Quick notes, commands, when speed matters

### **F10** - Enhanced Mode 🆕
- **Smart**: Context-aware processing with SG-Lang
- **Accurate**: Proper terminology correction (Gemini, Claude, API, etc.)
- **Use for**: Emails, AI tools, technical content, when accuracy matters

### **Status Commands**
- **Super + F9**: Show raw mode status
- **Super + F10**: Show enhanced mode status

## 🧠 Enhanced Mode Features

### **Context-Aware Profiles**
- **AI Tools**: Corrects "Gemini", "Claude", "ChatGPT", technical terms
- **Gmail**: Professional email formatting, proper AI tool names
- **YouTube**: Casual tone, video terminology
- **VSCode/Windsurf**: Code comments, technical accuracy
- **General Browser**: Web terminology, minimal corrections

### **Smart Corrections**
- **Low temperature** (0.1): Minimal changes, preserves your voice
- **Technical terms**: "API", "endpoint", "framework", "algorithm"
- **AI tool names**: "Gemini" instead of "geminI", "Claude" instead of "clawed"
- **Context awareness**: Different behavior for different applications

## 🛠️ Configuration

### **SG-Lang Server**
- **Port**: 30000
- **Model**: Qwen3 1.7B
- **Temperature**: 0.1 (minimal changes)
- **Style**: OpenAI-compatible

### **Application Profiles Updated**
- All profiles now use SG-Lang
- Lower temperatures for accuracy
- Specialized terminology dictionaries
- Enhanced system prompts

## 📋 Usage Examples

### **Raw Mode (F9)**
```
Hold F9 → "list all files in current directory" → Release F9
Result: ls -la (instant, no processing)
```

### **Enhanced Mode (F10)**
```
Hold F10 → "ask gemini to write python code for api endpoint" → Release F10
Result: Ask Gemini to write Python code for API endpoint (corrected terminology)
```

### **Email in Gmail**
```
Hold F10 → "hey team just wanted to update you on the ai project we're using claude and gemini" → Release F10
Result: Hey team, just wanted to update you on the AI project. We're using Claude and Gemini. (professional formatting)
```

## 🔧 Verification Commands

### **Check Enhanced Mode Status**
```bash
./scripts/hypr-voice-control.sh status-enhanced
```

### **Check SG-Lang Configuration**
```bash
curl http://localhost:30000/v1/models
```

### **Test Control Script**
```bash
./scripts/hypr-voice-control.sh
```

## 🎯 Expected Behavior

### **What Gets Fixed**
- **AI tool names**: Gemini, Claude, ChatGPT → correct spelling
- **Technical terms**: API, endpoint, framework → correct terminology
- **Basic grammar**: Obvious transcription errors
- **Application context**: Professional for email, casual for chat

### **What Stays the Same**
- **Your writing style**: Preserved
- **Your voice**: Maintained
- **Content meaning**: Unchanged
- **Speed**: Still fast (small delay for AI processing)

## 🚨 Troubleshooting

### **Enhanced Mode Not Working**
1. Check SG-Lang server: `curl http://localhost:30000/v1/models`
2. Verify port: Ensure SG-Lang is on port 30000
3. Check logs: `tail -f /tmp/hypr-voice-client.log`

### **Keybindings Not Working**
1. Reload Hyprland: `hyprctl reload`
2. Check keybind config: `hyprctl binds | grep F1[09]`
3. Verify script permissions: `ls -la scripts/hypr-voice-control.sh`

### **Poor Transcription Quality**
1. Check microphone: `arecord -l`
2. Test audio: `./scripts/test_audio.sh`
3. Adjust RAW_MODE if needed: `export RAW_MODE=false`

## 🎉 Benefits

- **Speed when needed**: F9 for instant transcription
- **Accuracy when important**: F10 for smart corrections
- **Context awareness**: Different behavior for different apps
- **Technical accuracy**: Proper AI/tech terminology
- **Minimal changes**: Preserves your voice and style

## 🔄 Switching Between Modes

- **From Raw to Enhanced**: Just press F10 instead of F9
- **From Enhanced to Raw**: Just press F9 instead of F10
- **Check current mode**: Press Super+F9 or Super+F10

The system automatically detects which mode you're using and applies the appropriate processing!