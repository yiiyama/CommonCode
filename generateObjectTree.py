import re
import os

def setBranchFunc(obj, lowerName, varList, isArray):
    text = '  void\n  ' + obj + 'Vars'
    if isArray: text += 'Array'
    text += '''::setBranches(TTree& _tree)
  {
'''

    if isArray:
        text += '    _tree.Branch("''' + lowerName + '.size", &size, "' + lowerName + '.size/i");\n\n'

    for (type, name) in varList[obj]:
        branch = '    _tree.Branch("' + lowerName + '.' + name + '", '
        if not isArray: branch += '&'
        branch += name + ', "' + name
        if isArray: branch += '[' + lowerName + '.size]'
        branch += '/'

        if type == 'char':
            branch += 'B'
        elif type == 'signed char':
            branch += 'B'
        elif type == 'unsigned char':
            branch += 'b'
        elif type == 'short':
            branch += 'S'
        elif type == 'unsigned short':
            branch += 's'
        elif type == 'int':
            branch += 'I'
        elif type == 'unsigned' or type == 'unsigned int':
            branch += 'i'
        elif type == 'long':
            branch += 'L'
        elif type == 'unsigned long':
            branch += 'l'
        elif type == 'float':
            branch += 'F'
        elif type == 'double':
            branch += 'D'
        elif type == 'bool':
            branch += 'O'

        branch += '");\n'
        text += branch

    text += '  }\n\n'

    return text

def setAddressFunc(obj, lowerName, varList, isArray):
    text = '  void\n  ' + obj + 'Vars'
    if isArray: text += 'Array'
    text += '''::setAddress(TTree& _tree)
  {
    std::vector<TString> notFound;
'''
    
    if isArray:
        text += '    _tree.SetBranchAddress("' + lowerName + '.size", &size);\n\n'

    for (type, name) in varList[obj]:
        bName = lowerName + '.' + name
        text += '    if(_tree.GetBranchStatus("' + bName + '")) _tree.SetBranchAddress("' + bName + '", '
        if not isArray: text += '&'
        text += name + ');\n'
        text += '    else if(!_tree.GetBranch("' + bName + '")) notFound.push_back("' + bName + '");\n'

    text += '''
    for(unsigned iN(0); iN != notFound.size(); ++iN)
      std::cerr << "Branch " << notFound[iN] << " not found in input" << std::endl;
  }

'''

    return text

objects = ['Photon', 'Electron', 'Muon', 'Jet', 'Vertex']
susyObjects = {'Photon': 'Photon', 'Electron': 'Electron', 'Muon': 'Muon', 'Jet': 'PFJet', 'Vertex': 'Vertex'}

objectVars = file('ObjectVars.h')

classPat = re.compile('^[ ]*class[ ]+([a-zA-Z0-9]+)Vars[ ]*{')
cTorPat = re.compile('^[ ]*[a-zA-Z0-9]+Vars\([^,]+(,[ ]+Event.*|)\);')
varPat = re.compile('^[ ]*((?:unsigned[ ]|signed[ ]|)(?:bool|char|short|int|unsigned|long|float|double))[ ]+([a-zA-Z_][a-zA-Z0-9_]*);')

useEvent = dict()
varList = dict()

obj = ''
for line in objectVars:
    if '};' in line:
        obj = ''
        
    if obj:
        cTorMatch = cTorPat.match(line)
        if cTorMatch:
            useEvent[obj] = len(cTorMatch.group(1)) != 0
            
        varMatch = varPat.match(line)
        if varMatch:
            varList[obj].append((varMatch.group(1), varMatch.group(2)))
            
    lineMatch = classPat.match(line)
    if lineMatch and lineMatch.group(1) in objects:
        obj = lineMatch.group(1)
        varList[obj] = []

objectVars.close()

# GENERATE HEADER

headerContent = '''/* Auto-generated header file */
#ifndef ObjectTree_h
#define ObjectTree_h

#include "ObjectVars.h"

#include "TTree.h"
#include "TString.h"

namespace susy {

  unsigned const NMAX(512);
'''
 
for obj in objects:
    headerContent += '''
  class ''' + obj + '''VarsArray {
  public:
    ''' + obj + '''VarsArray() : size(0) {}
    ~''' + obj + '''VarsArray() {}
    void setBranches(TTree&);
    void setAddress(TTree&);
    void push_back(''' + obj + '''Vars const&);
    void clear() { size = 0; }
    ''' + obj + '''Vars at(unsigned) const;

    unsigned size;
'''

    for (type, name) in varList[obj]:
        headerContent += '''
    ''' + type + ' ' + name + '[NMAX];'

    headerContent += '''
  };

'''

headerContent += '''
  class ObjectTree {
  public:    
    ObjectTree();
    ~ObjectTree();

    void setOutput(TString const&,'''

for i in range(len(objects)):
    headerContent += ' bool = true'
    if i != len(objects) - 1:
        headerContent += ','
    else:
        headerContent += ');'

headerContent += '''
    void setOutput(TTree&,'''

for i in range(len(objects)):
    headerContent += ' bool = true'
    if i != len(objects) - 1:
        headerContent += ','
    else:
        headerContent += ');'

headerContent += '''
    static void setBranchStatus(TTree&,'''

for i in range(len(objects)):
    headerContent += ' bool = true'
    if i != len(objects) - 1:
        headerContent += ','
    else:
        headerContent += ');'

headerContent += '''
    void initEvent();
    void fill() { output_->Fill(); }'''

for obj in objects:
    lowerName = obj.lower()
    headerContent += '''
    void save(''' + obj + 'Vars const& _vars) { ' + lowerName + 'Array_.push_back(_vars); }'

for obj in objects:
    lowerName = obj.lower()
    headerContent += '''
    unsigned get''' + obj + 'Size() const { return ' + lowerName + 'Array_.size; }'

for obj in objects:
    lowerName = obj.lower()
    headerContent += '''
    ''' + obj + 'VarsArray const& get' + obj + 'Array() const { return ' + lowerName + 'Array_; }'

headerContent += '''
  private:
    void setBranches_('''

for i in range(len(objects)):
    headerContent += 'bool'
    if i != len(objects) - 1:
        headerContent += ', '
    else:
        headerContent += ');'

for obj in objects:
    lowerName = obj.lower()
    headerContent += '''
    ''' + obj + '''VarsArray ''' + lowerName + '''Array_;'''

headerContent += '''

    TTree* output_;
    bool ownOutput_;
  };

}

#endif
'''

headerFile = file('ObjectTree.h', 'w')
headerFile.write(headerContent)
headerFile.close()

# GENERATE SRC

cTors = dict()
pushBack = dict()
at = dict()

for obj in objects:
    cTorText = '  ' + obj + 'Vars::' + obj + '''Vars() :'''

    initList = ''
    for (type, name) in varList[obj]:
        initList += '''
    ''' + name + '('
        if type == 'float' or type == 'double':
            initList += '0.'
        elif type == 'bool':
            initList += 'false'
        else:
            initList += '0'

        initList += '),'

    initList = initList.rstrip(',')
    cTorText += initList
    cTorText += '''
  {
  }

'''
    cTors[obj] = cTorText

    pushBackText = '''  void
  ''' + obj + 'VarsArray::push_back(' + obj + '''Vars const& _vars)
  {
    if(size == NMAX - 1)
      throw Exception(Exception::kEventAnomaly, "Too many ''' + obj + '''s");
'''
    
    for (type, name) in varList[obj]:
        pushBackText += '''
    ''' + name + '[size] = _vars.' + name + ';'

    pushBackText += '''
    ++size;
  }

'''
    pushBack[obj] = pushBackText

    atText = '  ' + obj + '''Vars
  ''' + obj + '''VarsArray::at(unsigned _pos) const
  {
    if(_pos >= size)
      throw std::range_error("''' + obj + '''Vars out-of-bounds");
      
    ''' + obj + '''Vars vars;
'''

    for (type, name) in varList[obj]:
        atText += '''
    vars.''' + name + ' = ' + name + '[_pos];'

    atText += '''
    return vars;
  }

'''

    at[obj] = atText

preamble = '#include "ObjectVars.h"\n'

try:
    originalSrc = file('ObjectVars.cc', 'r')
    userDef = ''

    copy = False
    namespace = False
    for line in originalSrc:
        if 'namespace susy' in line:
            namespace = True
            
        if not namespace and 'ObjectVars.h' not in line and not re.match('^[ ]*/\*.*\*/[ ]*$', line):
            preamble += line

        if '/* START USER-DEFINED IMPLEMENTATION (DO NOT MODIFY THIS LINE) */' in line:
            copy = True

        if copy:
            userDef += line

        if '/* END USER-DEFINED IMPLEMENTATION (DO NOT MODIFY THIS LINE) */' in line:
            copy = False

    originalSrc.close()
    
except:
    userDef = '\n/* START USER-DEFINED IMPLEMENTATION (DO NOT MODIFY THIS LINE) */\n'

    for obj in objects:
        userDef += '''
  void
  ''' + obj + '''Vars::set(''' + susyObjects[obj] + ' const&'
        if useEvent[obj]:
            userDef += ', Event const&'

        userDef += ''')
  {
  }

  /*static*/
  ''' + obj + '''Vars::setBranchStatus(TTree&)
  {
  }

'''

    userDef += '/* END USER-DEFINED IMPLEMENTATION (DO NOT MODIFY THIS LINE) */\n'

# ObjectTree.cc

objTreeContent = '''/* Auto-generated source file */
#include "ObjectTree.h"
#include "Utilities.h"

#include "TFile.h"

#include <iostream>

namespace susy {

'''

for obj in objects:
    objTreeContent += setBranchFunc(obj, obj.lower(), varList, True)
    objTreeContent += setAddressFunc(obj, obj.lower(), varList, True)
    objTreeContent += pushBack[obj]
    objTreeContent += at[obj]

objTreeContent += '''
  ObjectTree::ObjectTree() :'''

for obj in objects:
    lowerName = obj.lower()
    objTreeContent += '''
    ''' + lowerName + '''Array_(),'''

objTreeContent += '''
    output_(0),
    ownOutput_(false)
  {
  }

  ObjectTree::~ObjectTree()
  {
    if(ownOutput_ && output_){
      TFile* outFile(output_->GetCurrentFile());
      outFile->cd();
      output_->Write();
      delete outFile;
    }
  }

  void
  ObjectTree::setOutput(TString const& _fileName'''

for obj in objects:
    objTreeContent += ', bool _set' + obj + '/* = true*/'

objTreeContent += ''')
  {
    ownOutput_ = true;

    TFile::Open(_fileName, "recreate");
    output_ = new TTree("objectVars", "Object ID variables");

    setBranches_('''

for obj in objects:
    objTreeContent += '_set' + obj + ', '

objTreeContent = objTreeContent.rstrip(', ')
objTreeContent += ''');
  }

  void
  ObjectTree::setOutput(TTree& _tree'''

for obj in objects:
    objTreeContent += ', bool _set' + obj + '/* = true*/'

objTreeContent += ''')
  {
    output_ = &_tree;

    setBranches_('''

for obj in objects:
    objTreeContent += '_set' + obj + ', '

objTreeContent = objTreeContent.rstrip(', ')
objTreeContent += ''');
  }

  /*static*/
  void
  ObjectTree::setBranchStatus(TTree& _input'''

for obj in objects:
    objTreeContent += ', bool _set' + obj + '/* = true*/'

objTreeContent += ''')
  {'''

for obj in objects:
    objTreeContent += '''
    if(_set''' + obj + ') ' + obj + 'Vars::setBranchStatus(_input);'

objTreeContent += '''
  }

  void
  ObjectTree::initEvent()
  {'''

for obj in objects:
    objTreeContent += '''
    ''' + obj.lower() + 'Array_.clear();'

objTreeContent += '''
  }

  void
  ObjectTree::setBranches_('''

for obj in objects:
    objTreeContent += 'bool _set' + obj + ', '

objTreeContent = objTreeContent.rstrip(', ') + ')'
objTreeContent += '''
  {'''

for obj in objects:
    objTreeContent += '''
    if(_set''' + obj + ') ' + obj.lower() + 'Array_.setBranches(*output_);'

objTreeContent += '''
  }

'''

objTreeContent += '}\n'

objTreeFile = file('ObjectTree.cc', 'w')
objTreeFile.write(objTreeContent)
objTreeFile.close()

# ObjectVars.cc

objVarsContent = '''/* Partially auto-generated source file - edit where indicated */
/* Add necessary inclusions below */
''' + preamble + '''namespace susy {

'''

for obj in objects:
    objVarsContent += cTors[obj]
    objVarsContent += setBranchFunc(obj, obj.lower(), varList, False)
    objVarsContent += setAddressFunc(obj, obj.lower(), varList, False)

objVarsContent += '\n'
objVarsContent += userDef
objVarsContent += '''
}
'''

objVarsFile = file('ObjectVars.cc', 'w')
objVarsFile.write(objVarsContent)
objVarsFile.close()
