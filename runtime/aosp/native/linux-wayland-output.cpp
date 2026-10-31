#include "linux-wayland-output.h"
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"
#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <functional>
#include <poll.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <unistd.h>
namespace archtv::aosp {
struct LinuxWaylandOutput::Impl {
    wl_display* display=nullptr;
    wl_registry* registry=nullptr;
    wl_compositor* compositor=nullptr;
    wl_shm* shm=nullptr;
    wl_output* output=nullptr;
    xdg_wm_base* wm=nullptr;
    wl_surface* surface=nullptr;
    xdg_surface* xsurface=nullptr;
    xdg_toplevel* top=nullptr;
    bool configured=false,closed=false;
    bool shm_xrgb=false;
    uint32_t output_name=0;
    int w=0,h=0,output_w=0,output_h=0,refresh_mhz=0,mm_w=0,mm_h=0;
    struct Buffer {wl_buffer* object=nullptr;void* data=MAP_FAILED;size_t bytes=0;int width=0,height=0;bool released=true;};
    Buffer buffers[2];
    bool Pump(const std::function<bool()>& done) {
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
        while(!closed) {
            if(wl_display_dispatch_pending(display)<0)return false;
            if(done())return true;
            while(wl_display_prepare_read(display)!=0) {
                if(wl_display_dispatch_pending(display)<0)return false;
            }
            int flushed=wl_display_flush(display);
            if(flushed<0 && errno!=EAGAIN){wl_display_cancel_read(display);return false;}
            auto left=std::chrono::duration_cast<std::chrono::milliseconds>(deadline-std::chrono::steady_clock::now()).count();
            if(left<=0){wl_display_cancel_read(display);errno=ETIMEDOUT;return false;}
            pollfd p{wl_display_get_fd(display),static_cast<short>(POLLIN|(flushed<0?POLLOUT:0)),0};
            int n=poll(&p,1,static_cast<int>(left));
            if(n<0){wl_display_cancel_read(display);if(errno==EINTR)continue;return false;}
            if(n==0){wl_display_cancel_read(display);errno=ETIMEDOUT;return false;}
            if(p.revents&(POLLERR|POLLHUP|POLLNVAL)){wl_display_cancel_read(display);errno=EPIPE;return false;}
            if(p.revents&POLLIN){if(wl_display_read_events(display)<0)return false;}
            else wl_display_cancel_read(display);
        }
        errno=ENODEV;return false;
    }
    bool Poll() {
        if(!display || closed){errno=ENODEV;return false;}
        if(wl_display_dispatch_pending(display)<0)return false;
        while(wl_display_prepare_read(display)!=0)if(wl_display_dispatch_pending(display)<0)return false;
        int flushed=wl_display_flush(display);
        if(flushed<0 && errno!=EAGAIN){wl_display_cancel_read(display);return false;}
        pollfd p{wl_display_get_fd(display),POLLIN,0};int n=poll(&p,1,0);
        if(n<0){wl_display_cancel_read(display);return errno==EINTR;}
        if(n==0){wl_display_cancel_read(display);return !closed;}
        if(p.revents&(POLLERR|POLLHUP|POLLNVAL)){wl_display_cancel_read(display);closed=true;errno=EPIPE;return false;}
        if(p.revents&POLLIN){if(wl_display_read_events(display)<0)return false;}
        else wl_display_cancel_read(display);
        return wl_display_dispatch_pending(display)>=0 && !closed;
    }
    bool Sync() {
        bool done=false;auto* cb=wl_display_sync(display);
        if(!cb)return false;
        static const wl_callback_listener listener{[](void* p,wl_callback*,uint32_t){*static_cast<bool*>(p)=true;}};
        wl_callback_add_listener(cb,&listener,&done);bool ok=Pump([&]{return done;});wl_callback_destroy(cb);return ok;
    }
    static void Global(void* data,wl_registry* r,uint32_t name,const char* interface,uint32_t version) {
        auto& s=*static_cast<Impl*>(data);
        if(!std::strcmp(interface,"wl_compositor") && !s.compositor)s.compositor=static_cast<wl_compositor*>(wl_registry_bind(r,name,&wl_compositor_interface,std::min(version,4u)));
        else if(!std::strcmp(interface,"wl_shm") && !s.shm) {
            s.shm=static_cast<wl_shm*>(wl_registry_bind(r,name,&wl_shm_interface,1));
            static const wl_shm_listener listener{[](void* p,wl_shm*,uint32_t format){if(format==WL_SHM_FORMAT_XRGB8888)static_cast<Impl*>(p)->shm_xrgb=true;}};
            if(!s.shm){s.closed=true;return;}
            wl_shm_add_listener(s.shm,&listener,&s);
        } else if(!std::strcmp(interface,"xdg_wm_base") && !s.wm) {
            s.wm=static_cast<xdg_wm_base*>(wl_registry_bind(r,name,&xdg_wm_base_interface,1));
            static const xdg_wm_base_listener listener{[](void*,xdg_wm_base* wm,uint32_t serial){xdg_wm_base_pong(wm,serial);}};
            if(!s.wm){s.closed=true;return;}
            xdg_wm_base_add_listener(s.wm,&listener,&s);
        } else if(!std::strcmp(interface,"wl_output") && !s.output && version>=2) {
            s.output_name=name;s.output=static_cast<wl_output*>(wl_registry_bind(r,name,&wl_output_interface,2));
            static const wl_output_listener listener{
                [](void* p,wl_output*,int32_t,int32_t,int32_t mmw,int32_t mmh,int32_t,const char*,const char*,int32_t){auto& s=*static_cast<Impl*>(p);s.mm_w=mmw;s.mm_h=mmh;},
                [](void* p,wl_output*,uint32_t flags,int32_t w,int32_t h,int32_t refresh){if(flags&WL_OUTPUT_MODE_CURRENT){auto& s=*static_cast<Impl*>(p);s.output_w=w;s.output_h=h;s.refresh_mhz=refresh;}},
                [](void*,wl_output*){},[](void*,wl_output*,int32_t){},nullptr,nullptr};
            if(!s.output){s.closed=true;return;}
            wl_output_add_listener(s.output,&listener,&s);
        }
    }
    bool Connect(int fd) {
        int type=0;socklen_t size=sizeof(type);sockaddr_storage addr{};socklen_t length=sizeof(addr);
        if(getsockopt(fd,SOL_SOCKET,SO_TYPE,&type,&size)!=0 || type!=SOCK_STREAM || getpeername(fd,reinterpret_cast<sockaddr*>(&addr),&length)!=0 || addr.ss_family!=AF_UNIX){close(fd);errno=EINVAL;return false;}
        display=wl_display_connect_to_fd(fd);if(!display)return false;
        registry=wl_display_get_registry(display);if(!registry)return false;
        static const wl_registry_listener listener{Global,[](void* p,wl_registry*,uint32_t n){auto& s=*static_cast<Impl*>(p);if(n==s.output_name)s.closed=true;}};
        wl_registry_add_listener(registry,&listener,this);
        if(!Sync() || !Sync())return false;
        if(!compositor || !shm || !shm_xrgb || !wm || !output || output_w<=0 || output_h<=0){errno=ENODEV;return false;}
        surface=wl_compositor_create_surface(compositor);if(!surface)return false;xsurface=xdg_wm_base_get_xdg_surface(wm,surface);if(!xsurface)return false;
        static const xdg_surface_listener sl{[](void* p,xdg_surface* xs,uint32_t serial){auto& s=*static_cast<Impl*>(p);xdg_surface_ack_configure(xs,serial);s.configured=true;}};
        xdg_surface_add_listener(xsurface,&sl,this);top=xdg_surface_get_toplevel(xsurface);if(!top)return false;
        static const xdg_toplevel_listener tl{
            [](void* p,xdg_toplevel*,int32_t w,int32_t h,wl_array*){auto& s=*static_cast<Impl*>(p);s.w=w>0?w:s.output_w;s.h=h>0?h:s.output_h;},
            [](void* p,xdg_toplevel*){static_cast<Impl*>(p)->closed=true;}};
        xdg_toplevel_add_listener(top,&tl,this);xdg_toplevel_set_title(top,"ArchTV native output");xdg_toplevel_set_app_id(top,"org.archtv.native-output");xdg_toplevel_set_fullscreen(top,output);wl_surface_commit(surface);
        return Pump([&]{return configured && w>0 && h>0;});
    }
    bool Allocate(Buffer& b) {
        if(w<=0 || h<=0 || w>8192 || h>8192 || size_t(w)*h>16777216){errno=EOVERFLOW;return false;}
        b.width=w;b.height=h;b.bytes=size_t(w)*h*4;int fd=memfd_create("archtv-wayland-output",MFD_CLOEXEC|MFD_ALLOW_SEALING);if(fd<0)return false;
        if(ftruncate(fd,b.bytes)!=0){close(fd);return false;}
        b.data=mmap(nullptr,b.bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
        if(b.data==MAP_FAILED){close(fd);return false;}
        auto* pool=wl_shm_create_pool(shm,fd,static_cast<int32_t>(b.bytes));close(fd);if(!pool)return false;
        b.object=wl_shm_pool_create_buffer(pool,0,w,h,w*4,WL_SHM_FORMAT_XRGB8888);wl_shm_pool_destroy(pool);if(!b.object)return false;
        static const wl_buffer_listener listener{[](void* p,wl_buffer*){static_cast<Buffer*>(p)->released=true;}};
        wl_buffer_add_listener(b.object,&listener,&b);return true;
    }
    bool Commit(const uint32_t* pixels,int width,int height,int stride) {
        if(!display || closed || !pixels || width!=w || height!=h || stride<w || size_t(stride)*height>67108864){errno=EINVAL;return false;}
        if(!Pump([&]{return buffers[0].released || buffers[1].released;}))return false;
        auto& b=buffers[buffers[0].released?0:1];
        if(!b.object && !Allocate(b))return false;
        if(b.width!=w || b.height!=h || b.bytes!=size_t(w)*h*4){errno=EAGAIN;return false;} // resize needs new allocation, never overwrite an in-use buffer.
        for(int y=0;y<h;++y)std::memcpy(static_cast<uint32_t*>(b.data)+size_t(y)*w,pixels+size_t(y)*stride,size_t(w)*4);
        bool frame=false;auto* cb=wl_surface_frame(surface);if(!cb)return false;
        static const wl_callback_listener listener{[](void* p,wl_callback*,uint32_t){*static_cast<bool*>(p)=true;}};
        wl_callback_add_listener(cb,&listener,&frame);b.released=false;wl_surface_attach(surface,b.object,0,0);wl_surface_damage(surface,0,0,w,h);wl_surface_commit(surface);
        bool ok=Pump([&]{return frame;});wl_callback_destroy(cb);return ok;
    }
    ~Impl() {
        if(top)xdg_toplevel_destroy(top);if(xsurface)xdg_surface_destroy(xsurface);if(surface)wl_surface_destroy(surface);
        for(auto& b:buffers){if(b.object)wl_buffer_destroy(b.object);if(b.data!=MAP_FAILED)munmap(b.data,b.bytes);}
        if(output)wl_output_destroy(output);if(wm)xdg_wm_base_destroy(wm);if(shm)wl_shm_destroy(shm);if(compositor)wl_compositor_destroy(compositor);if(registry)wl_registry_destroy(registry);if(display)wl_display_disconnect(display);
    }
};
LinuxWaylandOutput::LinuxWaylandOutput():impl_(std::make_unique<Impl>()){}
LinuxWaylandOutput::~LinuxWaylandOutput()=default;
bool LinuxWaylandOutput::Connect(int fd){if(impl_->display){close(fd);errno=EALREADY;return false;}return impl_->Connect(fd);}
int LinuxWaylandOutput::width()const{return impl_->w;}
int LinuxWaylandOutput::height()const{return impl_->h;}
int LinuxWaylandOutput::refresh_millihz()const{return impl_->refresh_mhz;}
int LinuxWaylandOutput::dpi_x()const{return impl_->mm_w>0?int(impl_->output_w*25.4/impl_->mm_w):-1;}
int LinuxWaylandOutput::dpi_y()const{return impl_->mm_h>0?int(impl_->output_h*25.4/impl_->mm_h):-1;}
bool LinuxWaylandOutput::Poll(){return impl_->Poll();}
bool LinuxWaylandOutput::CommitCpu(const uint32_t* p,int w,int h,int stride){return impl_->Commit(p,w,h,stride);}
}
