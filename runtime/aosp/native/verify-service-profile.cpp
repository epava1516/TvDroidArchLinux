// Static profile validation using original AOSP parsers. Never starts services or actions.
#include "init.h"
#include "builtins.h"
#include <android-base/logging.h>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv) {
    android::base::InitLogging(argv,android::base::StderrLogger);
    if(argc<2)return 64;
    android::init::ActionManager actions;
    android::init::ServiceList services;
    android::init::Action::set_function_map(&android::init::GetBuiltinFunctionMap());
    auto parser=android::init::CreateParser(actions,services);
    bool readable=true;
    for(int i=1;i<argc;++i) {
        auto result=parser.ParseConfigFile(argv[i]);
        std::cout<<"PROFILE_FILE path="<<std::quoted(argv[i])<<" read_ok="<<result.ok()<<'\n';
        if(!result.ok()){std::cerr<<result.error().message()<<'\n';readable=false;}
    }
    // CheckAllCommands invokes handlers; the runtime map must never be called here.
    for(const auto& service:services) {
        std::cout<<"SERVICE name="<<std::quoted(service->name())<<" executable="<<std::quoted(service->args().at(0))<<" uid="<<service->uid()<<" gid="<<service->gid()<<" pid="<<service->pid()<<" flags="<<service->flags()<<" supplementary=";
        for(auto gid:service->supp_gids())std::cout<<gid<<',';
        std::cout<<'\n';
        if(service->pid()!=0)return 70;
    }
    std::cout<<"PROFILE_RESULT services="<<services.size()<<" actions="<<actions.size()<<" parse_errors="<<parser.parse_error_count()<<" builtin_value_checks=not_performed"<<" NO_SERVICE_OR_ACTION_EXECUTION\n";
    return readable && parser.parse_error_count()==0 ? 0 : 2;
}
