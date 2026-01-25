# Claude Context Search Test Documentation

## 🎯 **Test Purpose**
This document tracks the **Claude Context search system issue** where search results are not respecting dataset parameters and consistently returning content from the dominant `ai-docs` dataset.

---

## 📊 **Current Status**

### ✅ **Working Components**
- [x] Dataset creation (all datasets created successfully)
- [x] Content ingestion (sitemap crawling works)
- [x] Vector generation (embeddings created)
- [x] Dataset isolation verification (TTS test passed)

### ❌ **Broken Component**
- [ ] **Search system** - returns wrong dataset content

---

## 🔍 **Test Cases**

### **Test 1: Dataset Isolation (✅ PASSED)**
```bash
# Search for TTS providers in ai-docs (should NOT find TTS info)
claudeContext_search(
    project="Hypr-Voice",
    dataset="ai-docs",
    query="TTS voice provider KOKORO ELEVENLABS"
)
# Result: Generic audio tokens (✅ CORRECT - no TTS providers found)
```

### **Test 2: Sitemap Ingestion (✅ PASSED)**
```bash
# Ingest Inception Labs sitemap
claudeContext_crawl(
    url="https://docs.inceptionlabs.ai/sitemap.xml",
    dataset="inception-docs"
)
# Result: 4 chunks created successfully (✅ CORRECT)
```

### **Test 3: Search Dataset Isolation (❌ FAILED)**
```bash
# Search for Inception Labs content in inception-docs
claudeContext_search(
    project="Hypr-Voice",
    dataset="inception-docs",
    query="Inception Labs AI documentation"
)
# Expected: Inception Labs docs content
# Actual: Pydantic AI documentation (❌ BROKEN)
```

### **Test 4: GitHub Repo Search (❌ FAILED)**
```bash
# Search for GitHub repo content in perplexity-claude
claudeContext_search(
    project="Hypr-Voice",
    dataset="perplexity-claude",
    query="Zykairotis Perplexity claude github"
)
# Expected: GitHub repository code
# Actual: Pydantic AI documentation (❌ BROKEN)
```

---

## 📈 **Dataset Status Overview**

| Dataset | Chunks | Status | Search Working |
|---------|--------|--------|----------------|
| **ai-docs** | 9,761 | ✅ Active | ❌ Dominates all searches |
| **main** | 0 | ✅ Active | ❌ Empty |
| **perplexity-claude** | 1,247 | ✅ Active | ❌ Returns ai-docs content |
| **inception-docs** | 4 | ✅ Active | ❌ Returns ai-docs content |

---

## 🎯 **Root Cause Identified**

### **The Problem**
The search system **ignores the dataset parameter** and returns results from the largest dataset (`ai-docs`) regardless of the specified dataset.

### **Evidence**
1. **Ingestion works**: All datasets created and populated correctly
2. **Dataset isolation works**: TTS search correctly excluded TTS content from ai-docs
3. **Search broken**: All searches return `ai-docs` content regardless of dataset parameter

### **Technical Issue**
Search algorithm prioritizes **global project search** over **dataset-scoped search**, likely due to:
- Incorrect search configuration
- Dataset parameter being ignored
- Vector database mapping issues
- Search engine prioritizing larger datasets

---

## 🛠️ **Next Steps for Debugging**

### **1. Verify Dataset IDs**
```bash
mcp__claude-context__claudeContext_listDatasets
# Check if datasets have unique IDs
```

### **2. Test Force Dataset Parameter**
```bash
# Test if dataset parameter can be forced
claudeContext_search(
    project="Hypr-Voice",
    dataset="inception-docs",
    query="Inception Labs",
    force_dataset=True  # If parameter exists
)
```

### **3. Check Search Configuration**
```bash
# Examine search system configuration
# Check if default search scope is project-wide instead of dataset-scoped
```

### **4. Verify Vector Database Mapping**
```bash
# Check if chunks are properly mapped to datasets in the vector database
# Verify dataset-specific collections or filtering
```

---

## 🎯 **Expected Behavior After Fix**

| Dataset | Search Query | Expected Results |
|---------|-------------|-----------------|
| **ai-docs** | "Pydantic AI" | Pydantic AI documentation |
| **inception-docs** | "Inception Labs" | Inception Labs documentation |
| **perplexity-claude** | "GitHub repo" | GitHub repository code |

---

## 📝 **Test Results Log**

### **Date**: 2025-11-08
- **Test 1**: ✅ Dataset isolation working
- **Test 2**: ✅ Sitemap ingestion working
- **Test 3**: ❌ Search dataset isolation broken
- **Test 4**: ❌ GitHub repo search broken
- **Conclusion**: Search system needs to be fixed to respect dataset parameters

---

## 🔍 **Commands for Future Testing**

```bash
# Test dataset isolation
mcp__claude-context__claudeContext_search(
    project="Hypr-Voice",
    dataset="inception-docs",
    query="docs.inceptionlabs.ai"
)

# Verify datasets
mcp__claude-context__claudeContext_listDatasets

# Test search behavior
mcp__claude-context__claudeContext_search(
    project="Hypr-Voice",
    dataset="perplexity-claude",
    query="github repository"
)
```

---

**Status**: 🚨 **SEARCH SYSTEM ISSUE IDENTIFIED** - Needs investigation and fix.