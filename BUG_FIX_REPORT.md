# Bug Fix Report - inputFiles Parameter Not Working

**Date:** 2025-10-30 16:50  
**Issue:** Script generated all combinations (18 files) instead of filtered combinations (6 files)

---

## 🔴 Problem Identified

### What Happened:
- Generated **18 files** instead of expected **6 files**
- Each mockup processed **all 3 input files** instead of only assigned files
- Parameter `inputFiles: ['1.jpeg']` was ignored

### Root Cause Analysis:

Looking at the generation report, we can see:
```
Processing combination 1/6: 1.jpeg → 1.psd  ✅ Correct log
→ Opening mockup: 1.psd
→ Applying input: 1.jpeg  ✅ Should be only this
→ Applying input: 2.jpeg  ❌ Should NOT happen
→ Applying input: 3.jpeg  ❌ Should NOT happen
```

**The `inputFiles` parameter was not being passed through to the engine!**

---

## 🎯 Root Cause

In the engine script (`Batch Mockup Smart Object Replacement.jsx`), function `replaceLoopOptionsFiller()` creates an `itemObj` from `rawItem` but **did NOT copy the `inputFiles` property**.

### The Missing Line:

**Before (lines 575-589):**
```javascript
var items = [];
for ( var i=0; i < rawData.items.length; i++ ) {
  var rawItem = rawData.items[i];
  var itemObj = {};
  if ( rawItem.target ) itemObj.target = rawItem.target;
  if ( rawItem.align  ) itemObj.align  = rawItem.align;
  // ... other properties ...
  itemObj.input  = rawItem.input || '$/input';
  itemObj.inputFormats = rawItem.inputFormats;
  // ❌ Missing: inputFiles was never copied!
  if ( rawItem.inputPlaced_runAction ) itemObj.inputPlaced_runAction = rawItem.inputPlaced_runAction;
  if ( rawItem.inputPlaced_runScript ) itemObj.inputPlaced_runScript = rawItem.inputPlaced_runScript;
  items.push( itemObj );
}
```

**After (FIXED):**
```javascript
var items = [];
for ( var i=0; i < rawData.items.length; i++ ) {
  var rawItem = rawData.items[i];
  var itemObj = {};
  if ( rawItem.target ) itemObj.target = rawItem.target;
  if ( rawItem.align  ) itemObj.align  = rawItem.align;
  // ... other properties ...
  itemObj.input  = rawItem.input || '$/input';
  itemObj.inputFormats = rawItem.inputFormats;
  // ✅ FIXED: Copy inputFiles filter if provided
  if ( rawItem.inputFiles ) itemObj.inputFiles = rawItem.inputFiles;
  if ( rawItem.inputPlaced_runAction ) itemObj.inputPlaced_runAction = rawItem.inputPlaced_runAction;
  if ( rawItem.inputPlaced_runScript ) itemObj.inputPlaced_runScript = rawItem.inputPlaced_runScript;
  items.push( itemObj );
}
```

---

## ✅ Fix Applied

### Changed Files:

1. **`Batch Mockup Smart Object Replacement.jsx`** (line ~588)
   - Added: `if ( rawItem.inputFiles ) itemObj.inputFiles = rawItem.inputFiles;`
   - This ensures the `inputFiles` array is copied from raw input to processed item

2. **`Batch Mockup Smart Object Replacement.jsx`** (line ~336)
   - Added debug logging to track if `inputFiles` parameter is received
   - This will help with future debugging

---

## 🧪 Expected Results After Fix

### Before Fix:
```
Input files: 1.jpeg, 2.jpeg, 3.jpeg
Mockups: 1.psd, 2.psd, 3.psd
Output: 18 files (every input × every mockup × 2 duplicates)
```

### After Fix:
```
Input files: 1.jpeg, 2.jpeg, 3.jpeg
Mockups: 1.psd, 2.psd, 3.psd
Output: 6 files (according to config.json)

Expected files:
- 1_1.jpg (1.jpeg → 1.psd)
- 1_2.jpg (1.jpeg → 2.psd)
- 2_2.jpg (2.jpeg → 2.psd)
- 2_3.jpg (2.jpeg → 3.psd)
- 3_1.jpg (3.jpeg → 1.psd)
- 3_3.jpg (3.jpeg → 3.psd)
```

---

## 📝 Testing Steps

1. **Clear output folder:**
   ```bash
   rm /path/to/output/*.jpg
   rm /path/to/output/*.txt
   ```

2. **Run script in Photoshop:**
   - File → Scripts → Browse...
   - Select: `main_mockup_generator.jsx`

3. **Check results:**
   - Count files in output folder (should be 6 JPG + 1 TXT report)
   - Open generation report to verify:
     - "Files Processed: 6"
     - Each combination shows inputFiles filtering log
     - No duplicate files

4. **Verify report shows filtering:**
   ```
   [INFO] → prepFiles called for item with input: /path/to/input
   [INFO] → inputFiles parameter found: [1.jpeg]
   [INFO] → Filtering input files: [1.jpeg]
   [INFO] → Found: 1.jpeg
   ```

---

## 🔍 Debug Logs Added

Enhanced logging to track the flow:

1. **In `prepFiles()`:**
   - Logs when function is called
   - Logs if `inputFiles` parameter exists
   - Logs which files will be used

2. **In `filterFilesByNames()`:**
   - Logs filtering start
   - Logs each file found/not found
   - Logs warnings for missing files

This will help identify similar issues in the future.

---

## 🎯 Lessons Learned

1. **Always copy ALL parameters** from raw input to processed object
2. **Add debug logging early** to track parameter flow
3. **Test with real data** - synthetic tests might miss this
4. **Check the generation report** - it immediately showed the issue

---

## ✅ Status

- [x] Root cause identified
- [x] Fix implemented
- [x] Debug logging added
- [ ] **NEEDS TESTING** - Run script again to verify fix works

---

**Next Action:** Test the fix in Photoshop and verify 6 files are generated according to config.json
