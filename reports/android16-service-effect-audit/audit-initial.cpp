// Read-only audit of declarations accepted by original AOSP service/action parsers.
#include "init.h"
#include "builtins.h"
#include "service_parser.h"
#include "action_parser.h"
#include "service-profile-audit.h"
#include <android-base/logging.h>
#include <cstdio>
#include <iostream>
static void string(const std::string& value) {
    std::cout<<'"';
    for (unsigned char c:value) {
        if (c=='"' || c=='\\') std::cout<<'\\'<<c;
        else if (c<32) { char escaped[7]; std::snprintf(escaped,sizeof(escaped),"\\u%04x",c); std::cout<<escaped; }
        else std::cout<<c;
    }
    std::cout<<'"';
}
static void tokens(const std::vector<std::string>& values) {
    std::cout<<'['; bool comma=false;
    for (const auto& value:values) { if(comma) std::cout<<','; string(value); comma=true; }
    std::cout<<']';
}
int main(int argc,char** argv) {
    android::base::InitLogging(argv,android::base::StderrLogger);
    if(argc<2) return 64;
    using namespace android::init;
    ActionManager actions; ServiceList services;
    std::vector<archtv::aosp::ProfileSection> sections;
    Action::set_function_map(&GetBuiltinFunctionMap());
    auto parser=CreateParser(actions,services);
    parser.AddSectionParser("service",std::make_unique<archtv::aosp::AuditedSectionParser>(
        "service",std::make_unique<ServiceParser>(&services,GetSubcontext()),sections));
    parser.AddSectionParser("on",std::make_unique<archtv::aosp::AuditedSectionParser>(
        "on",std::make_unique<ActionParser>(&actions,GetSubcontext()),sections));
    bool readable=true;
    for(int i=1;i<argc;++i) if(!parser.ParseConfigFile(argv[i]).ok()) readable=false;
    // AOSP may retain partial service/action entries after errors; export no manifest then.
    if(!readable || parser.parse_error_count()!=0) {
        std::cout<<"AUDIT_REJECTED errors="<<parser.parse_error_count()<<" readable="<<readable<<'\n';
        return 2;
    }
    std::cout<<"PROFILE_AUDIT {\"schema\":1,\"admission_status\":\"not_evaluated\",\"sections\":[";
    bool comma=false;
    for(const auto& s:sections) {
        if(comma) std::cout<<','; comma=true;
        std::cout<<"{\"kind\":";string(s.kind);std::cout<<",\"filename\":";string(s.filename);
        std::cout<<",\"line\":"<<s.line<<",\"header\":";tokens(s.header);std::cout<<",\"lines\":[";
        bool inner=false;
        for(const auto& line:s.lines) {
            if(inner) std::cout<<',';inner=true;
            std::cout<<"{\"line\":"<<line.line<<",\"tokens\":";tokens(line.tokens);std::cout<<'}';
        }
        std::cout<<"]}";
    }
    std::cout<<"],\"services\":[";comma=false;
    for(const auto& s:services) {
        if(s->pid()!=0) return 70;
        if(comma)std::cout<<',';comma=true;
        std::cout<<"{\"name\":";string(s->name());std::cout<<",\"uid\":"<<s->uid()<<",\"gid\":"<<s->gid()
          <<",\"flags\":"<<s->flags()<<",\"pid\":0}";
    }
    std::cout<<"],\"actions\":"<<actions.size()<<",\"execution\":\"none\"}\n";
    return 0;
}
