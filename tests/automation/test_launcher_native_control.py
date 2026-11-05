"""Own ATL1 decoder/socket/worker host regressions, not Android execution."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CPP = r'''
#include "linux-launcher-control.h"
#include <cassert>
#include <iostream>
using namespace archtv::aosp;
using namespace archtv::aosp::launcher_wire;
void word(std::vector<uint8_t>& b,uint32_t value){value=htonl(value);auto* p=reinterpret_cast<uint8_t*>(&value);b.insert(b.end(),p,p+4);}
void text(std::vector<uint8_t>& b,const std::string& s){word(b,s.size());b.insert(b.end(),s.begin(),s.end());}
void entry(std::vector<uint8_t>& b,const std::string& component="com.example/com.example.Main"){
 text(b,component);text(b,"Aplicación 日本語");text(b,"android.intent.category.LAUNCHER");
}
int main(){
 assert(Utf8("Aplicación 日本語"));
 for(auto bad:{std::string("\xc0\xaf",2),std::string("\xed\xa0\x80",3),std::string("\xf4\x90\x80\x80",4),std::string("\xe2\x82",2)})assert(!Utf8(bad));
 std::vector<uint8_t> b;word(b,1);entry(b);std::vector<LauncherEntry> entries;
 assert(Catalog(b,entries)&&entries.size()==1&&entries[0].label=="Aplicación 日本語");
 auto trailing=b;trailing.push_back(0);assert(!Catalog(trailing,entries)&&entries.empty());
 for(size_t size=0;size<b.size();size++){auto partial=b;partial.resize(size);assert(!Catalog(partial,entries));}
 std::vector<uint8_t> duplicate;word(duplicate,2);entry(duplicate);entry(duplicate);assert(!Catalog(duplicate,entries));
 std::vector<uint8_t> excessive;word(excessive,513);assert(!Catalog(excessive,entries));
 std::vector<uint8_t> oversized;word(oversized,1);word(oversized,1025);assert(!Catalog(oversized,entries));
 assert(!Component("/class")&&!Component("package/")&&!Component("package/class/extra"));
 assert(!Component(std::string("package/class\0extra",19)));
 assert(OriginalLauncherRequest(2,0,"com.example/Main").status==LauncherStatus::Rejected);
 assert(OriginalLauncherRequest(1,1,"unexpected").status==LauncherStatus::Rejected);
 assert(OriginalLauncherRequest(2,1,"com.example/Main",std::chrono::steady_clock::now()).status==LauncherStatus::Unavailable);
 int fd[2];assert(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,fd)==0);
 std::thread producer([&]{if(send(fd[1],"ab",2,MSG_NOSIGNAL)!=2){perror("first socketpair send");abort();}std::this_thread::sleep_for(std::chrono::milliseconds(10));if(send(fd[1],"cd",2,MSG_NOSIGNAL)!=2){perror("second socketpair send");abort();}close(fd[1]);});
 char bytes[5]{};size_t count=0;assert(!Transfer(fd[0],bytes,5,false,std::chrono::steady_clock::now()+std::chrono::seconds(2),count));
 assert(count==4 && std::string(bytes,4)=="abcd");close(fd[0]);producer.join();
 {
   LinuxLauncherWorker worker;
   assert(!worker.Submit(3,1));assert(!worker.Submit(2,1,"invalid"));
   assert(worker.Submit(1,1));assert(!worker.Submit(1,1));assert(!worker.Submit(1,0));
   // Read-only request in the host test namespace. No original runtime is
   // launched; lack of authenticated endpoint must never become a success.
   std::vector<LinuxLauncherWorker::Completion> replies;
   auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(12);
   while(replies.empty() && std::chrono::steady_clock::now()<deadline){replies=worker.Poll();std::this_thread::sleep_for(std::chrono::milliseconds(5));}
   assert(replies.size()==1 && replies[0].sequence==1 && replies[0].reply.status==LauncherStatus::Unavailable);
 }
 std::cout<<"Host ATL1 parsing/fragmented EOF/expired request/worker replay checks passed; no original Binder or MAC acceptance\n";
}
'''

class NativeLauncherControl(unittest.TestCase):
    def test_actual_native_decoder_transport_and_worker(self):
        with tempfile.TemporaryDirectory(prefix='archtv-native-launcher-') as directory:
            work = pathlib.Path(directory)
            source = work / 'check.cpp'
            source.write_text(CPP)
            executable = work / 'check'
            subprocess.run(['g++', '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror',
                            '-I'+str(ROOT / 'runtime/aosp/native'), str(source), '-o', str(executable)],
                           check=True, capture_output=True, timeout=60)
            result = subprocess.run([str(executable)], capture_output=True,
                                    text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('worker replay checks passed', result.stdout)

if __name__ == '__main__':
    unittest.main()
