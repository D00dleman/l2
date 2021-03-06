<template>
  <div id="check-backend"/>
</template>

<script lang="ts">
import Vue from 'vue';
import { mapGetters } from 'vuex';
import Component from 'vue-class-component';
import * as actions from '@/store/action-types';
import { POSITION } from 'vue-toastification/src/ts/constants';

@Component({
  computed: mapGetters(['authenticated', 'user_data']),
  data() {
    return {
      userIsIdle: false,
      hasError: false,
      aliveTimer: null,
    };
  },
})
export default class CheckBackend extends Vue {
  authenticated: boolean;

  userIsIdle: boolean;

  hasError: boolean;

  aliveTimer: number | void;

  user_data: any;

  mounted() {
    setTimeout(() => this.check(), 8000);
  }

  check() {
    if (this.aliveTimer) {
      clearTimeout(this.aliveTimer);
    }

    if (this.$route.name === 'login' && this.authenticated) {
      const urlParams = new URLSearchParams(window.location.search);
      const nextPath = urlParams.get('next');
      this.$router.push(nextPath || { name: 'menu' });
      return;
    }

    window.$.ajax({
      method: 'GET',
      url: '/mainmenu/',
      cache: false,
      statusCode: {
        500: () => {
          this.$toast.clear();
          this.$toast.error('Сервер недоступен. Ошибка 500. Ожидайте доступность сервера.', {
            position: POSITION.BOTTOM_RIGHT,
            timeout: this.userIsIdle ? 300000 : 20000,
            icon: true,
          });

          if (!this.hasError) {
            this.hasError = true;
            this.$store.dispatch(actions.INC_LOADING);
          }
          window.$('input').blur();
        },
        502: () => {
          this.$toast.clear();
          this.$toast.error('Сервер недоступен. Ошибка 502. Ожидайте доступность сервера.', {
            position: POSITION.BOTTOM_RIGHT,
            timeout: this.userIsIdle ? 300000 : 20000,
            icon: true,
          });

          if (!this.hasError) {
            this.hasError = true;
            this.$store.dispatch(actions.INC_LOADING);
          }
          window.$('input').blur();
        },
      },
    }).fail(jqXHR => {
      if (jqXHR.status === 502 || jqXHR.status === 500) return;
      this.$toast.clear();
      this.$toast.error('Сервер недоступен. Ошибка связи с сервером. Сообщите администратору о проблеме', {
        position: POSITION.BOTTOM_RIGHT,
        timeout: this.userIsIdle ? 300000 : 20000,
        icon: true,
      });

      if (!this.hasError) {
        this.hasError = true;
        this.$store.dispatch(actions.INC_LOADING);
      }
      window.$('input').blur();
    }).done(data => {
      if (!this.authenticated && String(data).startsWith('OK')) {
        const urlParams = new URLSearchParams(window.location.search);
        const nextPath = urlParams.get('next');
        this.$router.push(nextPath || { name: 'menu' });
      }

      if (this.authenticated && !String(data).startsWith('OK')) {
        this.$router.push(`/ui/login?next=${encodeURIComponent(window.location.href.replace(window.location.origin, ''))}`);
        return;
      }

      if (
        this.authenticated
        && this.user_data
        && !this.user_data.loading
        && data !== `OK:${this.user_data.username}`
      ) {
        window.location.reload();
      }

      if (this.hasError) {
        this.$toast.clear();
        this.hasError = false;
        this.$toast.success('Сервер доступен', {
          position: POSITION.BOTTOM_RIGHT,
          timeout: 10000,
          icon: true,
        });
        this.$store.dispatch(actions.DEC_LOADING);
      }
    }).always(() => {
      this.aliveTimer = setTimeout(() => this.check(), this.userIsIdle ? 300000 : 20000);
    });
  }
}
</script>

<style scoped>
#check-backend {
  display: none;
}
</style>
